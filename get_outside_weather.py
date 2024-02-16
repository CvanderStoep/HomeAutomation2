import requests
import json

from influxdb_client import Point
from private_info import logging_file


def outside_weather(city="Delft"):
    from private_info import web_url
    complete_url = web_url + city
    response = requests.get(complete_url)
    x = response.json()
    # print("========================")
    # print(json.dumps(x, indent=2))
    # print("========================")
    y = x["main"]
    wind_speed = float(x["wind"]["speed"])
    wind_direction = (x["wind"]["deg"])
    current_temperature = round(y["temp"] - 273.15, 2)  # convert K to deg C
    weather_type = x["weather"][0]["main"]
    humidity = (x["main"]["humidity"])
    pressure = x["main"]["pressure"]
    with open(logging_file, "a") as f:
        print(f'openweathermap data: {city= }, {current_temperature= }', file=f)

    data_point = [Point("temperature").tag("location", city).field("temperature", current_temperature),
                  Point("pressure").tag("location", city).field("pressure", pressure),
                  Point("humidity").tag("location", city).field("humidity", humidity),
                  Point("weather_type").tag("location", city).field("weather_type", weather_type),
                  Point("wind").tag("location", city).field("direction", wind_direction),
                  Point("wind").tag("location", city).field("speed", wind_speed)]

    return data_point


if __name__ == '__main__':
    print(outside_weather())
