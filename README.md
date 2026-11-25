# Home Automation Project
(HUE, INFLUXDB, SOLARPANEL, GRAFANA, DOCKER, DOCKER COMPOSE)

Collects live data every minute and stores it in InfluxDB; Grafana visualizes it.
Everything runs in Docker containers on a Raspberry Pi.

## Data sources
* City weather data from the OpenWeatherMap API (`get_outside_weather.py`)
* Weather data from Buienradar (`get_buienradar.py`)
* Hue temperature sensors (`get_hue_temp.py`)
* Hue lights on/off (`get_hue_lights.py`)
* Solar panel data from the inverter's Wi-Fi logger (`InverterExport.py` + `InfluxDBOutput.py`)

The main loop is `realtimemonitoring.py`.

## Configuration
* `config.cfg` – non-secret settings: measurement interval, Buienradar location,
  Hue sensor IDs (section `[monitoring]` / `[hue_temperature_sensors]`) and the inverter settings.
* Private files (not in git): `.env`, `private_info.py`, `.python_hue`, `docker-compose.yml`.
  They are copied to the Pi with `deploy-private-files.command`.
  `private_info.py` and `.python_hue` are mounted into the container, not baked into the image.

## Logging
Logs go to stdout: `sudo docker logs -f realtimemonitoring`.
Set `LOG_LEVEL=DEBUG` in `docker-compose.yml` to also log all measured values.

## Installation on the Raspberry Pi
```sh
sudo apt-get update -y
sudo apt install docker.io docker-compose -y
git clone https://github.com/CvanderStoep/HomeAutomation2
docker network create ha_network     # the shared network must exist
```
Then run `deploy-private-files.command` on the Mac to copy the private files.

## Start / update
```sh
cd ~/HomeAutomation2
git pull
sudo docker compose up --build -d
```
The Grafana dashboard has to be imported manually.
