# Grafana-dashboard: back-up

`home-automation.json` is een **back-up** van het dashboard "Home automation logging RP400"
zoals het op de Raspberry Pi (productie) staat. Grafana laadt dit bestand **niet** automatisch:
het dashboard zelf staat in de Grafana-database van elke installatie, zodat de Mac nooit het
dashboard op de Pi kan overschrijven.

- Formaat: Grafana 13 dashboard v2 (`dashboard.grafana.app/v2`), uid `DtSJnhzgz`.
- Gemaakt van: Pi, generatie 133 (laatst aangepast 2026-11-18).

## Back-up bijwerken
Na een wijziging op de Pi: in Grafana op de Pi het dashboard openen, **Export > Export as JSON**,
opslaan als dit bestand en committen.

## Terugzetten
In Grafana: **Dashboards > New > Import**, dit bestand uploaden. Het dashboard gebruikt de
datasource met uid `FcHP1367k` ("InfluxDB RP400"), die via provisioning altijd aanwezig is.
