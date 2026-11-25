from influxdb_client import Point
from private_info import logging_file

# Sensoren op basis van hun uniqueid (hardware-adres). Die blijft gelijk als een sensor
# opnieuw wordt gekoppeld, in tegenstelling tot het sensor-ID op de bridge.
TEMP_SENSORS = {
    "00:17:88:01:02:03:29:c8-02-0402": "ground_floor",  # was sensor-ID 17
    "00:17:88:01:06:f6:6a:51-02-0402": "first_floor",   # was sensor-ID 75
    "00:17:88:01:02:02:52:a6-02-0402": "second_floor",  # was sensor-ID 8
}


def hue_temp(bridge):
    temperatures = {}
    for sensor_id, sensor in bridge.get_sensor().items():
        location = TEMP_SENSORS.get(sensor.get("uniqueid"))
        if location is None:
            continue
        temperature = sensor["state"].get("temperature")
        if temperature is None:
            continue
        temperatures[location] = (sensor_id, temperature / 100)  # temp in degC

    # Een ontbrekende sensor (bijv. lege batterij) wordt gelogd; de andere worden wel weggeschreven.
    missing = set(TEMP_SENSORS.values()) - set(temperatures)

    with open(logging_file, "a") as f:
        print(file=f)
        if missing:
            print(f"Hue temperatuursensor(en) niet gevonden: {', '.join(sorted(missing))}", file=f)
        for location, (sensor_id, temperature) in temperatures.items():
            print(f'Temperature Sensor[{sensor_id}] - {location}: ', temperature, file=f)
        print(file=f)

    data_point = [Point("hue_temperature").tag("sensor", location).field("temperature", temperature)
                  for location, (sensor_id, temperature) in temperatures.items()]

    return data_point
