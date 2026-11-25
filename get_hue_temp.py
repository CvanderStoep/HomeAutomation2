import logging

from influxdb_client import Point

logger = logging.getLogger(__name__)


def hue_temp(bridge, sensors):
    """Lees de Hue-temperatuursensoren uit.

    Args:
        bridge: verbonden phue Bridge
        sensors (dict): uniqueid -> locatie (sectie [hue_temperature_sensors] in config.cfg)

    Een ontbrekende sensor (bijv. lege batterij) wordt gelogd; de andere worden wel teruggegeven.
    """
    temperatures = {}
    for sensor_id, sensor in bridge.get_sensor().items():
        location = sensors.get(sensor.get("uniqueid"))
        if location is None:
            continue
        temperature = sensor["state"].get("temperature")
        if temperature is None:
            continue
        temperatures[location] = (sensor_id, temperature / 100)  # temp in degC

    missing = set(sensors.values()) - set(temperatures)
    if missing:
        logger.warning('Hue temperatuursensor(en) niet gevonden: %s', ', '.join(sorted(missing)))
    for location, (sensor_id, temperature) in temperatures.items():
        logger.debug('Temperature Sensor[%s] - %s: %s', sensor_id, location, temperature)

    return [Point("hue_temperature").tag("sensor", location).field("temperature", temperature)
            for location, (sensor_id, temperature) in temperatures.items()]
