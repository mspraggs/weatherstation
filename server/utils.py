import math

import pugsql

import config


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
    sea_level_air_pressure = round(raw_reading['air_pressure'] / pressure_ratio, 2)

    hydrated_reading = raw_reading.copy()
    hydrated_reading['sea_level_air_pressure'] = sea_level_air_pressure

    return hydrated_reading


def get_db_queries():
    queries = pugsql.module(config.QUERIES_PATH)
    queries.connect(f'sqlite:///{config.DB_PATH}')
    return queries
