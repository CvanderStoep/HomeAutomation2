#
# Get live data from the following sources:
# -City weather data using openweathermap api
# -Hue light sensor data
# -Hue temperature sensor data
# -Solarpanel data
#
# Output is send to InfluxDB version 2!!
# Output is visualized using InfluxDB and Grafana
#

import time
from datetime import datetime

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
from private_info import token, logging_file

client2 = InfluxDBClient(url=DB_url, token=token)
write_api = client2.write_api(write_options=SYNCHRONOUS)

try:
    inverter_exporter = InverterExport('config.cfg')  # connect to the solar inverter
except Exception as e:
    with open(logging_file, "a") as f:
        print(e, file=f)

if __name__ == '__main__':
    time_delay = 60 #seconds

    # connect to hue bridge
    try:
        bridge = initbridge()
    except Exception as e:
        with open(logging_file, "a") as f:
            print(e, file=f)

    with open(logging_file, "a") as f:
        print(bridge.username, file=f)
    # start_time = None  # time.time() make sure this runs at the start of the program
    while True:
        with open(logging_file, "a") as f:
            print(datetime.now(), file=f)
            print(datetime.now())

        # get outside weather data from the various cities using open weather site
        data_point = []
        try:
            for city in cities:
                data_point.append(outside_weather(city))
            write_api.write(bucket=bucket, org=org, record=data_point)
        except Exception as e:
            with open(logging_file, "a") as f:
                print(e, file=f)

        try:
            data_point = outside_buienradar()
            write_api.write(bucket=bucket, org=org, record=data_point)
        except Exception as e:
            with open(logging_file, "a") as f:
                print(e, file=f)
            pass

        # get inside temperature data from the hue bridge
        try:
            data_point = hue_temp(bridge)
            write_api.write(bucket=bucket, org=org, record=data_point)
        except Exception as e:
            with open(logging_file, "a") as f:
                print(e, file=f)

        # get status of the lights from the hue
        try:
            data_point = hue_lights(bridge)
            write_api.write(bucket=bucket, org=org, record=data_point)
        except Exception as e:
            with open(logging_file, "a") as f:
                print(e, file=f)

        # get data from the solar inverter
        try:
            inverter_exporter.run()
        except Exception as e:
            with open(logging_file, "a") as f:
                print(e, file=f)

        time.sleep(time_delay)  # sleep time in sec.
