from datetime import datetime
import dateutil
import math
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


def create_item(data):
    timestamp = data['timestamp'].astimezone(dateutil.tz.UTC)
    item = {
        'date': {'S': str(timestamp.date())},
        'timestamp': {'N': str(timestamp.timestamp())},
        'hour': {'N': str(timestamp.hour)},
        'minute': {'N': str(timestamp.minute)},
    }

    numeric_fields = list(data.keys())
    numeric_fields.remove('timestamp')

    for field in numeric_fields:
        value = data[field]
        entry = (
            {'N': str(value)}
            if value is not None
            and not math.isinf(value)
            and not math.isnan(value)
            else {'NULL': True}
        )
        item[field] = entry

    return item


if __name__ == '__main__':
    queries = utils.get_db_queries()
    timestamp = datetime.now(dateutil.tz.gettz(config.TIMEZONE))

    response = requests.get(config.SENSORS_URI)
    response.raise_for_status()
    temperature, relative_humidity, air_pressure = tuple(
        float(s.strip()) for s in response.text.split(',')
    )

    queries.create_reading(
        timestamp=timestamp.isoformat(),
        temperature=temperature,
        relative_humidity=relative_humidity,
        air_pressure=air_pressure,
        altitude=config.ALTITUDE,
    )

    item = create_item(
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

