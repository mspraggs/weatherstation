import datetime

import flask
import marshmallow
import pytz

import config
import utils


app = flask.Flask(__name__)


class ServerLocalDateTime(marshmallow.fields.NaiveDateTime):
    def __init__(self, timezone, *args, **kwargs):
        super().__init__(*args, timezone=pytz.utc, **kwargs)
        self._server_timezone = timezone

    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        obj = super()._deserialize(value, attr, data, **kwargs)
        return obj.replace(tzinfo=pytz.utc).astimezone(self._server_timezone)


class ReadingQuerySchema(marshmallow.Schema):
    from_timestamp = ServerLocalDateTime(
        format='iso', timezone=pytz.timezone(config.TIMEZONE), required=True,
    )
    to_timestamp = ServerLocalDateTime(
        format='iso', timezone=pytz.timezone(config.TIMEZONE), required=True,
    )
    interval = marshmallow.fields.Integer(required=False)

    ALLOWED_INTERVAL_CONSTRAINTS = [
        (1, 10),
        (7, 30),
        (14, 60),
    ]

    @marshmallow.validates_schema
    def validate_query(self, data, **kwargs):
        elapsed_days = (data['to_timestamp'] - data['from_timestamp']).days
        interval = data.get('interval')

        if interval and interval < 1:
            raise marshmallow.ValidationError(
                'interval must be greater than zero'
            )
        if elapsed_days <= 1:
            return

        if not interval:
            raise marshmallow.ValidationError(
                'timespans greater than 1 day must have interval set',
            )
        
        for ed_limit, i_limit in self.ALLOWED_INTERVAL_CONSTRAINTS:
            if elapsed_days > ed_limit and interval < i_limit:
                raise marshmallow.ValidationError(
                    f'timespans greater than {ed_limit} days must have '
                    f'interval of at least {i_limit}'
                )

        if elapsed_days > 30:
            raise marshmallow.ValidationError(
                'timespans greater than 30 days are forbidden'
            )


class ReadingSchema(marshmallow.Schema):
    timestamp = marshmallow.fields.DateTime(format='iso')
    altitude = marshmallow.fields.Float(missing=None)
    air_pressure = marshmallow.fields.Float(missing=None)
    relative_humidity = marshmallow.fields.Float(missing=None)
    temperature = marshmallow.fields.Float(missing=None)
    sea_level_air_pressure = marshmallow.fields.Float(optional=True)


@app.after_request
def default_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def localize_timestamp(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(pytz.timezone(config.TIMEZONE))

def parse_timestamp(timestamp):
    if timestamp.endswith('Z'):
        timestamp = timestamp[:-1]
    return localize_timestamp(
        datetime.datetime.fromisoformat(timestamp),
    )


def parse_query_params(args):
    return (
        parse_timestamp(args.get('from_timestamp', '')),
        parse_timestamp(args.get('to_timestamp', '')),
    )


@app.route('/readings')
def get_readings():
    try:
        query = ReadingQuerySchema().load(flask.request.args)
    except marshmallow.ValidationError as e:
        return f'Bad Request: {e.normalized_messages()}', 400

    queries = utils.get_db_queries()

    interval = query.get('interval')
    if interval:
        rows = ReadingSchema(many=True).load(
            queries.get_sparse_readings(
                from_timestamp=query['from_timestamp'].isoformat(),
                to_timestamp=query['to_timestamp'].isoformat(),
                nth_mins=interval,
            )
        )
    else:
        rows = ReadingSchema(many=True).load(
            queries.get_readings(
                from_timestamp=query['from_timestamp'].isoformat(),
                to_timestamp=query['to_timestamp'].isoformat(),
            )
        )

    return flask.jsonify(
        ReadingSchema(many=True).dump([utils.hydrate_reading(r) for r in rows])
    )


@app.route('/readings/latest')
def get_latest_reading():
    queries = utils.get_db_queries()
    row = ReadingSchema().load(queries.get_latest_reading())

    return flask.jsonify(ReadingSchema().dump(utils.hydrate_reading(row)))

if __name__ == '__main__':
    app.run(debug=True)
