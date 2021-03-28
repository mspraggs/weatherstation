import datetime
import dateutil
import json
import math
import os

import boto3
from boto3.dynamodb.conditions import And, Attr, Key
from botocore.config import Config


SEA_LEVEL_STD_TEMP = 288.16  # Kelvin
GRAV_ACCEL = 9.80665  # m / s**2
DRY_AIR_MOLAR_MASS = 0.02896968  # kg / mol
UNIV_GAS_CONST = 8.314462618  # J / (mol.K)


def translate_item(item):
    """
    Translates a reading into a format suitable for JSON serialisation.
    """
    timestamp = datetime.datetime.fromtimestamp(
        float(item['timestamp']), dateutil.tz.UTC,
    )
    return {
        'timestamp': timestamp.isoformat(),
        'altitude': float(item['altitude']),
        'temperature': float(item['temperature']),
        'relative_humidity': float(item['relative_humidity']),
        'air_pressure': float(item['air_pressure']),
    }


def hydrate_reading(raw_reading):
    altitude = raw_reading['altitude']
    pressure_ratio = math.exp(
        - GRAV_ACCEL * altitude * DRY_AIR_MOLAR_MASS
        / (SEA_LEVEL_STD_TEMP * UNIV_GAS_CONST)
    )
    air_pressure = raw_reading.get('air_pressure')
    sea_level_air_pressure = None
    if air_pressure:
        sea_level_air_pressure = round(air_pressure / pressure_ratio, 2)

    hydrated_reading = raw_reading.copy()
    hydrated_reading['sea_level_air_pressure'] = sea_level_air_pressure

    return hydrated_reading


def get_latest_reading():
    """
    Fetch weather data readings between the specified timestamps
    """
    resource = boto3.resource(
        'dynamodb',
        config=Config(region_name='eu-west-2'),
    )
    table = resource.Table(os.environ.get('TABLE_NAME'))

    inc = datetime.timedelta(days=-1)

    current_date = datetime.date.today()
    stop_date = current_date - datetime.timedelta(days=30)

    while current_date >= stop_date:
        response = table.query(
            KeyConditionExpression=Key('date').eq(str(current_date)),
        )
        items = response['Items']
        if len(items) > 0:
            return translate_item(max(items, key=lambda i: i['timestamp']))
        current_date += inc


def lambda_handler(event, context):
    """
    Implementation of GET /readings/latest.
    """

    latest_reading = get_latest_reading()

    if latest_reading is None:
        return {
            'statusCode': 404,
            'message': 'No reading found in last 30 days.'
        }

    return {
        'statusCode': 200,
        'body': json.dumps(hydrate_reading(latest_reading))
    }
