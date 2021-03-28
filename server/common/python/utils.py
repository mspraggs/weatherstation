import datetime
import dateutil
import math


SEA_LEVEL_STD_TEMP = 288.16  # Kelvin
GRAV_ACCEL = 9.80665  # m / s**2
DRY_AIR_MOLAR_MASS = 0.02896968  # kg / mol
UNIV_GAS_CONST = 8.314462618  # J / (mol.K)


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
