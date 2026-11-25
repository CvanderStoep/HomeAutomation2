#
# Get live data from the following sources:
# -City weather data using openweathermap api
# -City weather data from buienradar
# -Hue light sensor data
# -Hue temperature sensor data
# -Solarpanel data
#
# Output is send to InfluxDB version 2!!
# Output is visualized using InfluxDB and Grafana
#
# Instellingen (interval, Buienradar-locatie, Hue-sensoren) staan in config.cfg, sectie [monitoring].
#
# Logging gaat naar stdout (zichtbaar met `docker logs realtimemonitoring`).
# Niveau instelbaar met de omgevingsvariabele LOG_LEVEL (DEBUG, INFO, WARNING, ERROR);
# standaard INFO. Op DEBUG worden ook alle meetwaarden gelogd.
#

import configparser
import logging
import os
import time
from dataclasses import dataclass
from functools import partial

import InverterLib
import influx_db
from InverterExport import InverterExport
from get_buienradar import outside_buienradar
from get_hue_lights import hue_lights
from get_hue_temp import hue_temp
from get_outside_weather import outside_weather
from initbridge import initbridge
from private_info import cities

CONFIG_FILE = 'config.cfg'

logger = logging.getLogger('realtimemonitoring')


@dataclass
class Settings:
    interval: int
    buienradar_city: str
    buienradar_latitude: float
    buienradar_longitude: float
    hue_sensors: dict  # uniqueid -> locatie


def load_settings(path=CONFIG_FILE):
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(InverterLib.expand_path(path)):
        raise FileNotFoundError(path)
    monitoring = config['monitoring']
    return Settings(
        interval=monitoring.getint('interval', fallback=60),
        buienradar_city=monitoring.get('buienradar_city', fallback='Delft'),
        buienradar_latitude=monitoring.getfloat('buienradar_latitude'),
        buienradar_longitude=monitoring.getfloat('buienradar_longitude'),
        hue_sensors={uniqueid: location for location, uniqueid in config['hue_temperature_sensors'].items()},
    )


def setup_logging():
    level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    # Bibliotheken alleen laten melden als er iets mis is.
    for noisy in ('urllib3', 'influxdb_client', 'phue', 'buienradar'):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def log_error(source, e):
    logger.error('%s: %s: %s', source, type(e).__name__, e)


class Monitor:
    """Eén meetronde: alle bronnen uitlezen en in één keer naar InfluxDB schrijven."""

    def __init__(self, settings):
        self.settings = settings
        # Hue bridge en inverter worden (opnieuw) verbonden zolang dat nog niet gelukt is,
        # zodat een storing bij het opstarten de monitoring niet blokkeert.
        self.bridge = None
        self.inverter_exporter = None

    def connect(self, failed):
        if self.bridge is None:
            try:
                self.bridge = initbridge()  # connect to hue bridge
                logger.info('Verbonden met Hue bridge')
            except Exception as e:
                log_error('Hue bridge verbinden', e)
                failed.append('Hue bridge')

        if self.inverter_exporter is None:
            try:
                self.inverter_exporter = InverterExport(CONFIG_FILE)  # connect to the solar inverter
            except Exception as e:
                log_error('InverterExport starten', e)
                failed.append('Inverter')

    def sources(self):
        """Lijst van (naam, functie) die elk een lijst Points teruggeven."""
        s = self.settings
        sources = [(f'OpenWeatherMap {city}', partial(outside_weather, city)) for city in cities]
        sources.append(('Buienradar', partial(outside_buienradar, s.buienradar_city,
                                              s.buienradar_latitude, s.buienradar_longitude)))
        if self.bridge is not None:
            sources.append(('Hue temperatuur', partial(hue_temp, self.bridge, s.hue_sensors)))
            sources.append(('Hue lampen', partial(hue_lights, self.bridge)))
        return sources

    def run_cycle(self):
        failed = []
        self.connect(failed)

        # Elke bron apart, zodat één mislukte bron de andere niet tegenhoudt.
        points = []
        for name, read_source in self.sources():
            try:
                points.extend(read_source())
            except Exception as e:
                log_error(name, e)
                failed.append(name)

        if points:
            try:
                influx_db.write(points)
            except Exception as e:
                log_error('InfluxDB wegschrijven', e)
                failed.append('InfluxDB wegschrijven')

        # De inverter schrijft zelf weg via de InfluxDBOutput-plugin.
        if self.inverter_exporter is not None:
            try:
                self.inverter_exporter.run()
            except Exception as e:
                log_error('Inverter', e)
                failed.append('Inverter')

        if failed:
            logger.info('Meetronde klaar (%s punten), mislukt: %s', len(points), ', '.join(failed))
        else:
            logger.info('Meetronde klaar (%s punten)', len(points))


if __name__ == '__main__':
    setup_logging()
    settings = load_settings()
    monitor = Monitor(settings)

    logger.info('Gestart, meetinterval %s s', settings.interval)
    while True:
        monitor.run_cycle()
        time.sleep(settings.interval)
