#
# Get live data from the following sources:
# -City weather data using openweathermap api
# -Hue light sensor data
# -Hue temperature sensor data
# -Solarpanel data
#
# Output is send to InfluxDB version 2!!
# Output is visualized using InfluxDB iso Grafana
#

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from private_info import token
from private_info import org
from private_info import bucket
from private_info import DB_url

import time
from datetime import datetime
from initbridge import initbridge
from get_hue_temp import hue_temp
from get_hue_lights import hue_lights
from get_outside_weather import outside_weather
from get_meteo import outside_meteo
from private_info import cities

from InverterExport import InverterExport

client2 = InfluxDBClient(url=DB_url, token=token)
write_api = client2.write_api(write_options=SYNCHRONOUS)

inverter_exporter = InverterExport('config.cfg')  # connect to the solar inverter

retention_policy_default = None  # the temperature readings are stored indefinitely
retention_policy_one_week = "one-week"  # the light readings are stored one week

if __name__ == '__main__':

    # connect to hue bridge
    bridge = initbridge()
    print(bridge.username)
    start_time = time.time()
    while True:
        # get outside weather data from the various cities using open weather site
        data_point = []
        for city in cities:
            data_point.append(outside_weather(city))

        write_api.write(bucket=bucket, org=org, record=data_point)
        print(datetime.now())

        # get outside weather data from meteoserver for location Delft (every 24 hrs)
        current_time = time.time()
        if current_time - start_time >= 24*60*60:
            data_point = outside_meteo()
            write_api.write(bucket=bucket, org=org, record=data_point)
            start_time = current_time
        else:
            print('24 hrs not passed yet')

        # get inside temperature data from the hue bridge
        data_point = hue_temp(bridge)
        write_api.write(bucket=bucket, org=org, record=data_point)

        # get status of the lights from the hue
        data_point = hue_lights(bridge)
        write_api.write(bucket=bucket, org=org, record=data_point)

        inverter_exporter.run()

        time.sleep(60)  # sleep time in sec.
