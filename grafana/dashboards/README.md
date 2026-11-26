# Grafana-dashboard

`home-automation.json` is het dashboard "Home automation logging RP400" (uid `DtSJnhzgz`).
Dit bestand is de **enige bron**: bij `docker compose up` laadt Grafana op de Mac en op de Pi
precies deze versie (provisioning, zie `grafana/provisioning/dashboards/dashboards.yml`).

- Formaat: klassiek Grafana-dashboard-JSON (schemaVersion 42).
- Opslaan in de Grafana-interface staat uit (`allowUiUpdates: false`), zodat Grafana en git
  nooit uit elkaar lopen.

## Dashboard aanpassen
1. Pas het dashboard aan in Grafana (op de Mac of de Pi). Opslaan kan niet; dat is de bedoeling.
2. Kies **Export > Export as JSON** (klassiek formaat) en sla het op als dit bestand.
   Laat het veld `id` weg als het erin staat; `uid` moet `DtSJnhzgz` blijven.
3. Commit en push.
4. Op de Pi: `git pull`. Grafana neemt de nieuwe versie binnen een minuut over,
   een herstart is niet nodig. Op de Mac geldt hetzelfde.

## Let op
- Haal een dashboard nooit rechtstreeks uit `grafana.db`: in Grafana 13 kan de oude
  `dashboard`-tabel verouderd zijn. Gebruik de interface of de API
  (`GET /api/dashboards/uid/DtSJnhzgz`, veld `dashboard`).
- Verwijder of hernoem dit bestand niet: Grafana haalt het dashboard dan ook weg.
- Het dashboard gebruikt de datasource met uid `FcHP1367k` ("InfluxDB RP400"), die ook via
  provisioning wordt aangemaakt.
