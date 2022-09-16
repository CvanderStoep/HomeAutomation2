""""Reads the old solar monthly data from an Excel sheet exported from the Solar website"""

import requests
import pandas as pd
from datetime import datetime

from influxdb_client import Point
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from private_info import token
from private_info import org
from private_info import bucket
from private_info import DB_url


client2 = InfluxDBClient(url=DB_url, token=token)
write_api = client2.write_api(write_options=SYNCHRONOUS)


def old_solar_data(city="Delft"):
    df = pd.read_excel('Fam. van der Stoep-Maandelijkse statistieken-20220913.xlsx')
    df = df[['Bijgewerkte tijd', 'Productie(kWh)']]

    data_point = []
    for i, row in df.iterrows():
        time_stamp = row['Bijgewerkte tijd']
        power = row['Productie(kWh)']
        solar_time = datetime.strptime(time_stamp, "%Y/%m")
        time_stamp = str(solar_time.year) + "-" + str(solar_time.month) + "-01T00:00:00.000000Z"
        print(i, time_stamp, power)

        data_point.append(Point("solarhistory").tag("location", city).field("power", power).time(time_stamp))

    return data_point


if __name__ == '__main__':
    data_point = old_solar_data()
    write_api.write(bucket=bucket, org=org, record=data_point)

# Examples::
# Point.measurement("h2o").field("val", 1).time("2009-11-10T23:00:00.123456Z")
# Point.measurement("h2o").field("val", 1).time(1257894000123456000)
# Point.measurement("h2o").field("val", 1).time(datetime(2009, 11, 10, 23, 0, 0, 123456))
# Point.measurement("h2o").field("val", 1).time(1257894000123456000, write_precision=WritePrecision.NS)
