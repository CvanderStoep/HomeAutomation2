import requests
import json

from influxdb_client import Point


def outside_meteo(city="Delft"):
    # from private_info import complete_url  # combines api key and city for the temperature
    # from private_info import web_url
    # complete_url = web_url + city
    complete_url = 'https://data.meteoserver.nl/api/liveweer_synop.php?locatie=Delft&key=09491a4958&select=1'
    response = requests.get(complete_url)
    x = response.json()
    # f = open('meteo.json')
    # x = json.load(f)
    # print("========================")
    # print(json.dumps(x, indent=2))
    # print("========================")
    y = x["liveweer"][0]

    wind_speed = float(y["windms"])
    wind_direction = y["windrgr"]
    wind_gust = y["windstootms"]
    regen_24 = float(y["regen_24"])
    # city = y["plaats"]
    current_temperature = round(float(y["temp"]) ,2)
    print(f'{city= }, {current_temperature= }, {wind_speed= }, {regen_24= }')

    data_point = [Point("rainfall").tag("location", city).field("rainfall_24hr", regen_24)]
    #               Point("pressure").tag("location", city).field("pressure", pressure),
    #               Point("humidity").tag("location", city).field("humidity", humidity),
    #               Point("weather_type").tag("location", city).field("weather_type", weather_type),
    #               Point("wind").tag("location", city).field("direction", wind_direction),
    #               Point("wind").tag("location", city).field("speed", wind_speed)]

    return data_point


if __name__ == '__main__':
    print(outside_meteo())
