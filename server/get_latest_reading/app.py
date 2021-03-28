import datetime
import dateutil
import json
import math
import os

import boto3
from boto3.dynamodb.conditions import And, Attr, Key
from botocore.config import Config

import utils


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
            return utils.translate_item(
                max(items, key=lambda i: i['timestamp'])
            )
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
        'body': json.dumps(utils.hydrate_reading(latest_reading))
    }
