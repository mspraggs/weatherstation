import datetime
import dateutil
import json
import math
import os
import time

import boto3
from boto3.dynamodb.conditions import And, Attr, Key
from botocore.config import Config

import utils


def get_latest_reading():
    """
    Fetch weather data readings between the specified timestamps
    """
    start_time = time.time()
    resource = boto3.resource(
        'dynamodb',
        config=Config(region_name='eu-west-2'),
    )
    table = resource.Table(os.environ.get('TABLE_NAME'))

    item = table.get_item(
        Key={'date': '0000-00-00', 'timestamp': 0},
    ).get('Item')

    if item is not None:
        item['date'] = item.pop('latest_date')
        item['timestamp'] = item.pop('latest_timestamp')

    reading = item and utils.translate_item(item)

    finish_time = time.time()
    elapsed_time = finish_time - start_time
    print(f'Time spent fetching data from DynamoDB: {elapsed_time} seconds')

    return reading


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
        'body': json.dumps(utils.hydrate_reading(latest_reading))
    }
