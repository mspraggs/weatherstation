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


class ValidationError(Exception):
    """
    Raised when validating event parameters.
    """


def parse_timestamp(timestamp):
    """
    Parse provided timestamp into a datetime object.
    """
    is_utc = timestamp.endswith('Z')
    try:
        parsed_timestamp = datetime.datetime.fromisoformat(
            timestamp.rstrip('Z'),
        )
    except ValueError:
        raise ValidationError("Unable to parse timestamp.")

    if is_utc:
        parsed_timestamp.replace(tzinfo=dateutil.tz.UTC)

    return parsed_timestamp


def parse_interval(interval):
    """
    Parse the supplied interval into an int object.
    """
    try:
        return int(interval)
    except ValueError:
        raise ValidationError("Unable to parse interval.")


def validate_query_parameters(parameters):
    """
    Validate the provided query parameters.
    """
    from_timestamp = parameters['from_timestamp']
    to_timestamp = parameters['to_timestamp']
    interval = parameters.get('interval', 1)

    if to_timestamp < from_timestamp:
        raise ValidationError(
            'Expected \'to_timestamp\' to be equal to or greater than '
            '\'from_timestamp\'.'
        )

    if interval < 1:
        raise ValidationError(
            'Interval must be greater than zero.'
        )

    if not interval:
        raise ValidationError(
            'Missing \'interval\' parameter for timespan greater than one day.',
        )

    min_interval = utils.compute_min_interval(from_timestamp, to_timestamp)

    if interval < min_interval:
        raise ValidationError(
            f'Specified timespan requires \'interval\' parameter of at least '
            f'{min_interval}.'
        )

    if (to_timestamp - from_timestamp).days > 30:
        raise ValidationError(
            'Timespans greater than 30 days are forbidden.'
        )


def parse_query_parameters(parameters):
    """
    Parse and validate the provided query parameters.
    """
    from_timestamp = parameters.get('from_timestamp')
    if from_timestamp is None:
        raise ValidationError('Query missing \'from_timestamp\' parameter.')

    to_timestamp = parameters.get('to_timestamp')
    if to_timestamp is None:
        raise ValidationError('Query missing \'to_timestamp\' parameter.')

    from_timestamp = parse_timestamp(from_timestamp)
    to_timestamp = parse_timestamp(to_timestamp)

    interval = parameters.get('interval')
    interval = interval and parse_interval(interval)

    parsed_parameters = {
        'from_timestamp': from_timestamp,
        'to_timestamp': to_timestamp,
    }
    if interval is not None:
        parsed_parameters['interval'] = interval

    validate_query_parameters(parsed_parameters)

    return parsed_parameters


def get_data(from_timestamp, to_timestamp, interval):
    """
    Fetch weather data readings between the specified timestamps
    """
    start_time = time.time()
    resource = boto3.resource(
        'dynamodb',
        config=Config(region_name='eu-west-2'),
    )
    table = resource.Table(os.environ.get('TABLE_NAME'))

    minutes = [i for i in range(60) if i % interval == 0]
    query_params = {}
    if interval != 1:
        query_params['FilterExpression'] = Attr('minute').is_in(minutes)
    inc = datetime.timedelta(days=1)

    data = []

    current_date = from_timestamp.date()
    stop = to_timestamp.date()

    while current_date <= stop:
        response = table.query(
            KeyConditionExpression=And(
                Key('date').eq(str(current_date)),
                Key('timestamp').between(
                    int(from_timestamp.timestamp()),
                    int(to_timestamp.timestamp()),
                ),
            ),
            **query_params,
        )
        data.extend([utils.translate_item(i) for i in response['Items']])
        current_date += inc

    finish_time = time.time()
    elapsed_time = finish_time - start_time
    print(f'Time spent fetching data from DynamoDB: {elapsed_time} seconds')

    return data


def lambda_handler(event, context):
    """
    Implementation for GET /readings.
    """
    try:
        query_parameters = parse_query_parameters(
            event.get('queryStringParameters', {}),
        )
    except ValidationError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': str(e)}),
        }

    data = get_data(
        from_timestamp=query_parameters['from_timestamp'],
        to_timestamp=query_parameters['to_timestamp'],
        interval=query_parameters.get('interval', 1),
    )

    return {
        'statusCode': 200,
        'body': json.dumps([utils.hydrate_reading(r) for r in data]),
    }
