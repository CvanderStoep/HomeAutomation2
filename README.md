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
* `config.cfg` – non-secret settings: measurement interval, OpenWeatherMap cities, Buienradar location,
  solar location tag, Hue sensor IDs (section `[monitoring]` / `[hue_temperature_sensors]`) and the inverter settings.
* Private files (not in git): `.env`, `.python_hue`.
  They are copied to the Pi with `deploy-private-files.command`.
* Secrets (InfluxDB token, OpenWeatherMap API key, Hue bridge IP) live in `.env`;
  docker-compose passes them to the container as environment variables (see `env_config.py`).
  `.python_hue` is mounted into the container, not baked into the image.
* `requirements.txt` – dependencies of the Docker image; `requirements-import.txt` adds pandas etc.
  for the one-off script in `import old solar data/`.

## Grafana
* The InfluxDB datasource is provisioned from `grafana/provisioning/datasources/influxdb.yml`
  (token, org and bucket come from `.env`).
* The dashboard is provisioned from `grafana/dashboards/home-automation.json`. That file in git is
  the single source: the Mac and the Pi both load exactly this version. Saving in the Grafana UI is
  disabled; to change the dashboard, export it to that file and commit
  (see `grafana/dashboards/README.md`).

## Logging
Logs go to stdout: `sudo docker logs -f realtimemonitoring`.
Set `LOG_LEVEL=DEBUG` in `docker-compose.yml` to also log all measured values.

## Installation on the Raspberry Pi
```sh
sudo apt-get update -y
sudo apt install docker.io docker-compose -y
git clone https://github.com/CvanderStoep/monitoring
docker network create ha_network     # the shared network must exist
```
Then run `deploy-private-files.command` on the Mac to copy the private files.

## Start / update
```sh
cd ~/monitoring
git pull
sudo docker compose up --build -d
```
Datasource and dashboard are created automatically, also on a fresh install.

## Backup and restore (InfluxDB, Pi → Mac)
The Pi is production; the Mac keeps copies and can show the same data in Docker.
Backups (±1 GB each) are not in git; they go to `~/Library/CloudStorage/OneDrive-Persoonlijk/Documenten/13. Backup scripts` (OneDrive, so also off-site).

* `backup-influx-from-pi.command` – full `influx backup` on the Pi, streamed over ssh into
  `influx-backup-YYYY-MM-DD`. Every file is checked against the manifest (present, size, gzip).
  The Pi keeps running.
* `restore-influx-on-mac.command [influx-backup-YYYY-MM-DD]` – restores the newest backup (or the given one)
  with `influx restore --full` on the Mac. It makes a safety copy in `~/InfluxDB-veiligheidskopie` first,
  starts only `influxdb` and `grafana` (not `realtimemonitoring`), and prints the number of points and the
  last timestamp per measurement. Grafana on the Mac: http://localhost:3000.

Notes:
* Mac and Pi share the same `.env`, so the admin token is correct after `restore --full`.
* Don't run heavy queries over the full range (`range(start: 0)`) on the Pi; it runs out of memory.
  Do such checks on the Mac.
* Old backups and safety copies are not removed automatically.
