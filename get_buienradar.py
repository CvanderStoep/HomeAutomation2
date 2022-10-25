""""https://pypi.org/project/buienradar/"""


import requests

from influxdb_client import Point
from buienradar.buienradar import (get_data, parse_data)
from buienradar.constants import (CONTENT, RAINCONTENT, SUCCESS)


def outside_buienradar(city="Delft"):
    # minutes to look ahead for precipitation forecast
    # (5..120)
    timeframe = 45

    # gps-coordinates for the weather data (location Delft)
    latitude = 52.0067
    longitude = 4.3556

    result = get_data(latitude=latitude,
                      longitude=longitude,
                      )

    if result.get(SUCCESS):
        data = result[CONTENT]
        raindata = result[RAINCONTENT]
        result = parse_data(data, raindata, latitude, longitude, timeframe)
    distance = result["distance"]
    pressure = result["data"]["pressure"]
    windspeed = result["data"]["windspeed"]
    windforce = result["data"]["windforce"]
    windgust = result["data"]["windgust"]
    winddirection = result["data"]["winddirection"]
    rainlasthour = result["data"]["rainlasthour"]
    stationname = result["data"]["stationname"]
    temperature = result["data"]["temperature"]
    humidity = result["data"]["humidity"]
    rainlast24hour = result["data"]["rainlast24hour"]
    print(f'{stationname= }')

    print(f'buienradar data: {city= }, {pressure= }, {windspeed= }, {windgust= }, {rainlasthour= }, {winddirection= }')

    data_point = [Point("buienradar").tag("location", city).field("rainlasthour", rainlasthour),
                  Point("buienradar").tag("location", city).field("rainlast24hour", rainlast24hour),
                  Point("buienradar").tag("location", city).field("temperature", temperature),
                  Point("buienradar").tag("location", city).field("humidity", humidity),
                  Point("buienradar").tag("location", city).field("windforce", windforce),
                  Point("buienradar").tag("location", city).field("windspeed", windspeed),
                  Point("buienradar").tag("location", city).field("winddirection", winddirection),
                  Point("buienradar").tag("location", city).field("windgust", windgust)
                  ]
    return data_point


if __name__ == '__main__':
    outside_buienradar()
