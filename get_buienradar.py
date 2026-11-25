""""https://pypi.org/project/buienradar/"""


from influxdb_client import Point
from buienradar.buienradar import (get_data, parse_data)
from buienradar.constants import (CONTENT, MESSAGE, RAINCONTENT, SUCCESS)
from private_info import logging_file


def outside_buienradar(city="Delft", latitude=52.0067, longitude=4.3556):
    """Haal het actuele weer op bij het dichtstbijzijnde Buienradar-station.

    De standaardcoördinaten zijn die van Delft; geef bij een andere stad ook
    latitude/longitude mee, anders klopt de 'location'-tag niet met de data.
    """
    # minutes to look ahead for precipitation forecast
    # (5..120)
    timeframe = 45

    result = get_data(latitude=latitude,
                      longitude=longitude,
                      )
    if not result.get(SUCCESS):
        raise RuntimeError(f"Buienradar ophalen mislukt: {result.get(MESSAGE)}")

    result = parse_data(result[CONTENT], result[RAINCONTENT], latitude, longitude, timeframe)
    if not result.get(SUCCESS):
        raise RuntimeError(f"Buienradar data verwerken mislukt: {result.get(MESSAGE)}")

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
    with open(logging_file, "a") as f:
        print(f'{stationname= }, {distance= }', file=f)
        print(f'buienradar data: {city= }, {pressure= }, {windspeed= }, {windgust= }, {rainlasthour= }, {winddirection= }', file=f)

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
    print(outside_buienradar())
