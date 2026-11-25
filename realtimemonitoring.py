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
# Logging gaat naar stdout (zichtbaar met `docker logs realtimemonitoring`).
# Niveau instelbaar met de omgevingsvariabele LOG_LEVEL (DEBUG, INFO, WARNING, ERROR);
# standaard INFO. Op DEBUG worden ook alle meetwaarden gelogd.
#

import logging
import os
import time

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from InverterExport import InverterExport
from get_buienradar import outside_buienradar
from get_hue_lights import hue_lights
from get_hue_temp import hue_temp
from get_outside_weather import outside_weather
from initbridge import initbridge
from private_info import DB_url
from private_info import bucket
from private_info import cities
from private_info import org
from private_info import token

logger = logging.getLogger('realtimemonitoring')

client2 = InfluxDBClient(url=DB_url, token=token)
write_api = client2.write_api(write_options=SYNCHRONOUS)


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


if __name__ == '__main__':
    setup_logging()
    time_delay = 60 #seconds

    # Hue bridge en inverter worden in de loop (opnieuw) verbonden zolang dat nog niet
    # gelukt is, zodat een storing bij het opstarten de monitoring niet blokkeert.
    bridge = None
    inverter_exporter = None

    logger.info('Gestart, meetinterval %s s', time_delay)
    while True:
        failed = []

        if bridge is None:
            try:
                bridge = initbridge()  # connect to hue bridge
                logger.info('Verbonden met Hue bridge')
            except Exception as e:
                log_error('Hue bridge verbinden', e)
                failed.append('Hue bridge')

        if inverter_exporter is None:
            try:
                inverter_exporter = InverterExport('config.cfg')  # connect to the solar inverter
            except Exception as e:
                log_error('InverterExport starten', e)
                failed.append('Inverter')

        # get outside weather data from the various cities using open weather site
        # (per stad, zodat één mislukte stad de andere niet tegenhoudt)
        data_point = []
        for city in cities:
            try:
                data_point.extend(outside_weather(city))
            except Exception as e:
                log_error(f'OpenWeatherMap {city}', e)
                failed.append(f'OpenWeatherMap {city}')
        try:
            if data_point:
                write_api.write(bucket=bucket, org=org, record=data_point)
        except Exception as e:
            log_error('OpenWeatherMap wegschrijven', e)
            failed.append('OpenWeatherMap wegschrijven')

        try:
            data_point = outside_buienradar()
            write_api.write(bucket=bucket, org=org, record=data_point)
        except Exception as e:
            log_error('Buienradar', e)
            failed.append('Buienradar')

        if bridge is not None:
            # get inside temperature data from the hue bridge
            try:
                data_point = hue_temp(bridge)
                write_api.write(bucket=bucket, org=org, record=data_point)
            except Exception as e:
                log_error('Hue temperatuur', e)
                failed.append('Hue temperatuur')

            # get status of the lights from the hue
            try:
                data_point = hue_lights(bridge)
                write_api.write(bucket=bucket, org=org, record=data_point)
            except Exception as e:
                log_error('Hue lampen', e)
                failed.append('Hue lampen')

        # get data from the solar inverter
        if inverter_exporter is not None:
            try:
                inverter_exporter.run()
            except Exception as e:
                log_error('Inverter', e)
                failed.append('Inverter')

        if failed:
            logger.info('Meetronde klaar, mislukt: %s', ', '.join(failed))
        else:
            logger.info('Meetronde klaar')

        time.sleep(time_delay)  # sleep time in sec.
