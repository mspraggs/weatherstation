from datetime import datetime
import os
import sys

sys.path.append(os.getcwd())

import pugsql
import pytz
import requests

import config
import utils


if __name__ == '__main__':
    queries = utils.get_db_queries()
    timestamp = datetime.now(pytz.timezone(config.TIMEZONE))

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
