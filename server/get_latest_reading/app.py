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

    inc = datetime.timedelta(days=-1)

    current_date = datetime.date.today()
    stop_date = current_date - datetime.timedelta(days=30)
    reading = None

    while current_date >= stop_date:
        response = table.query(
            KeyConditionExpression=Key('date').eq(str(current_date)),
        )
        items = response['Items']
        if len(items) > 0:
            reading = utils.translate_item(
                max(items, key=lambda i: i['timestamp'])
            )
            break

        current_date += inc

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
