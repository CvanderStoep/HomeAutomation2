import logging

import requests

from influxdb_client import Point

logger = logging.getLogger(__name__)


def outside_weather(city="Delft"):
    from private_info import web_url
    complete_url = web_url + city
    # De URL bevat de API-key. Foutmeldingen van requests tonen de volledige URL,
    # dus die worden vervangen door een melding zonder URL (komt anders in de logs).
    try:
        # timeout voorkomt dat de hele meetloop blijft hangen als de API niet reageert
        response = requests.get(complete_url, timeout=10)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f'HTTP {e.response.status_code} {e.response.reason}') from None
    except requests.RequestException as e:
        raise RuntimeError(type(e).__name__) from None
    x = response.json()
    y = x["main"]
    wind_speed = float(x["wind"]["speed"])
    wind_direction = (x["wind"]["deg"])
    current_temperature = round(y["temp"] - 273.15, 2)  # convert K to deg C
    weather_type = x["weather"][0]["main"]
    humidity = (x["main"]["humidity"])
    pressure = x["main"]["pressure"]
    logger.debug('openweathermap data: city=%s, temperature=%s, weather=%s', city, current_temperature, weather_type)

    data_point = [Point("temperature").tag("location", city).field("temperature", current_temperature),
                  Point("pressure").tag("location", city).field("pressure", pressure),
                  Point("humidity").tag("location", city).field("humidity", humidity),
                  Point("weather_type").tag("location", city).field("weather_type", weather_type),
                  Point("wind").tag("location", city).field("direction", wind_direction),
                  Point("wind").tag("location", city).field("speed", wind_speed)]

    return data_point


if __name__ == '__main__':
    print(outside_weather())
