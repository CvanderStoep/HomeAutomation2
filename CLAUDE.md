# CLAUDE.md — monitoring

Communiceer in het Nederlands. Zie `README.md` voor installatie en details, en `../CLAUDE.md` voor het overzicht van
de hele setup.

## Wat dit is
InfluxDB 2.x, Grafana en `realtimemonitoring` (omvormer, Hue, weer) in één compose-file. InfluxDB (org `CVSIM`,
bucket `localdatadb2`) is het centrum van de setup: Home Assistant en `battery-revenue` lezen en schrijven hier ook.

## Namen en locaties
- Overal dezelfde naam: map `monitoring/` op de Mac, `/home/pi/monitoring` op de Pi, GitHub `CvanderStoep/monitoring`.
  Tot 2026-11-28 heette dit `inverter` (Mac) en `HomeAutomation2` (Pi en GitHub).
- De compose-`name:` is bewust `home-automation` en blijft dat: de volumes `home-automation_influxdb-storage`,
  `home-automation_influxdb.conf` en `home-automation_grafana-storage` hangen eraan.
- Grafana-dashboard en -datasource komen uit `grafana/` (provisioning, read-only in de UI). Wijzigen gaat via git.

## Deploy
- Op de Pi: `cd ~/monitoring && git pull && docker compose up --build -d`.
- `.env` en `.python_hue` staan niet in git; die gaan naar de Pi met `deploy-private-files.command`.
- De `*.command`-scripts (backup, restore, deploy) draaien alleen op de Mac.
- Map hernoemen of verplaatsen: eerst `docker compose down` (zonder `-v`), want de bind mounts (`.python_hue`,
  `grafana/`) hangen aan het absolute pad.

## Regels
- `.env` en `.python_hue` bevatten secrets: lezen en tonen mag, maar nooit committen of naar GitHub pushen.
- Op de Mac maar kort draaien: Mac en Pi die allebei de omvormer uitlezen kunnen botsen.
- Geen zware queries (bv. `range(start: 0)`) op de InfluxDB van de Pi; controles doen op de Mac-kopie.
