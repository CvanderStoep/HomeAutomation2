"""Gedeelde InfluxDB-verbinding voor alle meetbronnen (één client voor het hele programma)."""

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from private_info import DB_url, bucket, org, token

client = InfluxDBClient(url=DB_url, token=token)
_write_api = client.write_api(write_options=SYNCHRONOUS)


def write(points):
    """Schrijf een lijst met Points in één keer naar de bucket."""
    _write_api.write(bucket=bucket, org=org, record=points)
