# Grafana-dashboard: back-up

`home-automation.json` is een **back-up** van het dashboard "Home automation logging RP400"
zoals het op de Raspberry Pi (productie) staat. Grafana laadt dit bestand **niet** automatisch:
het dashboard zelf staat in de Grafana-database van elke installatie, zodat de Mac nooit het
dashboard op de Pi kan overschrijven.

- Formaat: klassiek Grafana-dashboard-JSON (schemaVersion 42), uid `DtSJnhzgz`.
- Gemaakt van: Pi, versie 134 (opgeslagen 2026-11-26), opgehaald via de Grafana-API.

## Back-up bijwerken
Altijd via Grafana zelf, nooit rechtstreeks uit `grafana.db` (in Grafana 13 kan de oude
`dashboard`-tabel verouderd zijn). Twee manieren:

- In Grafana op de Pi: dashboard openen, **Export > Export as JSON** (klassiek formaat),
  opslaan als dit bestand en committen.
- Via de API (met een Viewer-service-account-token):
  `GET http://raspberrypi400.local:3000/api/dashboards/uid/DtSJnhzgz` — gebruik het veld
  `dashboard` uit het antwoord en laat `id` weg.

## Terugzetten
In Grafana: **Dashboards > New > Import**, dit bestand uploaden. Het dashboard gebruikt de
datasource met uid `FcHP1367k` ("InfluxDB RP400"), die via provisioning altijd aanwezig is.
