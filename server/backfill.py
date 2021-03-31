from datetime import datetime
import dateutil
import os
import sys
import time

sys.path.append(os.getcwd())

import pugsql
import pytz
import requests

import boto3
from botocore.config import Config

import config
import utils


COLUMN_HEADINGS = (
    'timestamp',
    'temperature',
    'relative_humidity',
    'air_pressure',
    'altitude',
)
TABLE_NAME = 'weatherstation-dev-WeatherDataTable-MOBHMQJ76PGN'
# TABLE_NAME = 'weatherstation-prod-WeatherDataTable-1D0BRV6F7DK5C'
FROM_TIMESTAMP = None
TO_TIMESTAMP = None


def parse_line_to_reading(line):
    """
    Parse line to reading.
    """
    raw_data = line.split(',')
    reading = {}
    for l, d in zip(COLUMN_HEADINGS, raw_data):
        try:
            reading[l] = float(d)
        except ValueError:
            reading[l] = None
    reading['timestamp'] = datetime.fromtimestamp(
        reading['timestamp'], dateutil.tz.UTC,
    )
    return reading


if __name__ == '__main__':
    session = boto3.Session()
    client = session.client(
        'dynamodb',
        config=Config(region_name='eu-west-2'),
    )

    with open(config.CSV_PATH) as f:
        lines = f.readlines()

    readings = [parse_line_to_reading(l) for l in lines]
    readings = [
        r for r in readings
        if r['timestamp'].timestamp() >= (FROM_TIMESTAMP or 0.0)
        and r['timestamp'].timestamp() < (TO_TIMESTAMP or time.time())
    ]

    for reading in readings:
        print(f'Backfilling reading @ {reading["timestamp"].isoformat()}')
        item = utils.create_item(reading)
        client.put_item(TableName=TABLE_NAME, Item=item)
