from influxdb_client import Point
from private_info import logging_file


def hue_temp(bridge):

    sensors = bridge.get_sensor_objects('id')
    temp_sensor_first_floor = sensors[75].state['temperature'] / 100  # temp in degC
    temp_sensor_ground_floor = sensors[17].state['temperature'] / 100
    temp_sensor_second_floor = sensors[8].state['temperature'] / 100

    with open(logging_file, "a") as f:
        print(file=f)
        print('Temperature Sensor[8] - second_floor: ', temp_sensor_second_floor, file=f)
        print('Temperature Sensor[17] - ground_floor: ', temp_sensor_ground_floor, file=f)
        print('Temperature Sensor[75] - first_floor: ', temp_sensor_first_floor, file=f)
        print(file=f)


    data_point = [Point("hue_temperature").tag("sensor", "ground_floor").field("temperature", temp_sensor_ground_floor),
                  Point("hue_temperature").tag("sensor", "first_floor").field("temperature", temp_sensor_first_floor),
                  Point("hue_temperature").tag("sensor", "second_floor").field("temperature", temp_sensor_second_floor)
                  ]

    return data_point
