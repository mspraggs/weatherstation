from datetime import datetime
import dateutil
import math
import os
import sys

sys.path.append(os.getcwd())

import requests

import boto3
from botocore.config import Config

import config
import utils


if __name__ == '__main__':
    timestamp = datetime.now(dateutil.tz.gettz(config.TIMEZONE))

    response = requests.get(config.SENSORS_URI)
    response.raise_for_status()
    temperature, relative_humidity, air_pressure = tuple(
        float(s.strip()) for s in response.text.split(',')
    )

    with open(config.CSV_PATH, 'a') as f:
        line = ','.join([
            str(timestamp.timestamp()),
            str(temperature),
            str(relative_humidity),
            str(air_pressure),
            str(config.ALTITUDE),
        ])
        f.write(f'{line}\n')

    item = utils.create_item(
        {
            'timestamp': timestamp,
            'temperature': temperature,
            'air_pressure': air_pressure,
            'relative_humidity': relative_humidity,
            'altitude': config.ALTITUDE,
        }
    )

    session = boto3.Session()
    client = session.client(
        'dynamodb',
        config=Config(region_name='eu-west-2'),
    )
    client.put_item(
        TableName='weatherstation-prod-WeatherDataTable-1D0BRV6F7DK5C',
        Item=item,
    )

