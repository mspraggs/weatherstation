from datetime import datetime
import os
import sys

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
    reading['timestamp'] = datetime.fromtimestamp(reading['timestamp'])
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

    for reading in readings:
        item = utils.create_item(reading)
        client.put_item(TableName='weatherstation-dev-WeatherDataTable-MOBHMQJ76PGN', Item=item)
        #client.put_item(TableName='weatherstation-prod-WeatherDataTable-1D0BRV6F7DK5C', Item=item)
