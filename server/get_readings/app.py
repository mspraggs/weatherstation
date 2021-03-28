import datetime
import dateutil
import json
import math
import os

import boto3
from boto3.dynamodb.conditions import And, Attr, Key
from botocore.config import Config


ALLOWED_INTERVAL_CONSTRAINTS = [
    (1, 10),
    (7, 30),
    (14, 60),
]
SEA_LEVEL_STD_TEMP = 288.16  # Kelvin
GRAV_ACCEL = 9.80665  # m / s**2
DRY_AIR_MOLAR_MASS = 0.02896968  # kg / mol
UNIV_GAS_CONST = 8.314462618  # J / (mol.K)


class ValidationError(Exception):
    """
    Raised when validating event parameters.
    """


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
    """
    """
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
    elapsed_days = (
        parameters['to_timestamp'] - parameters['from_timestamp']
    ).days
    interval = parameters.get('interval')

    if interval and interval < 1:
        raise ValidationError(
            'Interval must be greater than zero.'
        )
    if elapsed_days <= 1:
        return

    if not interval:
        raise ValidationError(
            'Missing \'interval\' parameter for timespan greater than one day.',
        )

    for ed_limit, i_limit in ALLOWED_INTERVAL_CONSTRAINTS:
        if elapsed_days > ed_limit and interval < i_limit:
            raise ValidationError(
                f'Timespans greater than {ed_limit} days must have '
                f'\'interval\' parameter of at least {i_limit}'
            )

    if elapsed_days > 30:
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
    resource = boto3.resource(
        'dynamodb',
        config=Config(region_name='eu-west-2'),
    )
    table = resource.Table(os.environ.get('TABLE_NAME'))

    minutes = [i for i in range(60) if i % interval == 0]
    inc = datetime.timedelta(days=1)

    data = []

    current_date = from_timestamp.date()
    stop = to_timestamp.date() + inc

    while current_date < stop:
        response = table.query(
            KeyConditionExpression=And(
                Key('date').eq(str(current_date)),
                Key('timestamp').between(
                    int(from_timestamp.timestamp()),
                    int(to_timestamp.timestamp()),
                ),
            ),
            FilterExpression=Attr('minute').is_in(minutes),
        )
        data.extend([translate_item(i) for i in response['Items']])
        current_date += inc

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
        'body': json.dumps([hydrate_reading(r) for r in data]),
    }
