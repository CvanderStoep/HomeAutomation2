"""Secrets en verbindingsgegevens uit omgevingsvariabelen.

In Docker zet docker-compose deze variabelen (waarden uit .env). Lokaal laadt VS Code
.env in de terminal (instelling python.terminal.useEnvFile).

Variabelen:
    INFLUXDB_URL            standaard http://influxdb:8086 (containernaam op ha_network)
    INFLUXDB_TOKEN          of DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
    INFLUXDB_ORG            of DOCKER_INFLUXDB_INIT_ORG
    INFLUXDB_BUCKET         of DOCKER_INFLUXDB_INIT_BUCKET
    OPENWEATHERMAP_API_KEY
    HUE_BRIDGE_IP
"""

import os


def env(*names, default=None):
    """Waarde van de eerste gezette variabele uit names; fout als geen enkele gezet is."""
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    if default is not None:
        return default
    raise RuntimeError(f"Omgevingsvariabele ontbreekt: {' of '.join(names)} (zie .env)")


def influxdb_url():
    return env('INFLUXDB_URL', default='http://influxdb:8086')


def influxdb_token():
    return env('INFLUXDB_TOKEN', 'DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')


def influxdb_org():
    return env('INFLUXDB_ORG', 'DOCKER_INFLUXDB_INIT_ORG')


def influxdb_bucket():
    return env('INFLUXDB_BUCKET', 'DOCKER_INFLUXDB_INIT_BUCKET')


def openweathermap_api_key():
    return env('OPENWEATHERMAP_API_KEY')


def hue_bridge_ip():
    return env('HUE_BRIDGE_IP')
