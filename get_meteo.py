import requests

from influxdb_client import Point


def outside_meteo(city="Delft"):
    complete_url = 'https://data.meteoserver.nl/api/liveweer_synop.php?locatie=Delft&key=09491a4958&select=1'
    response = requests.get(complete_url)
    x = response.json()
    y = x["liveweer"][0]

    wind_speed = float(y["windms"])
    regen_24 = float(y["regen_24"])
    current_temperature = round(float(y["temp"]), 2)
    print(f'meteo data: {city= }, {current_temperature= }, {wind_speed= }, {regen_24= }')

    data_point = [Point("rainfall").tag("location", city).field("rainfall_24hr", regen_24)]

    return data_point


if __name__ == '__main__':
    print(outside_meteo())
