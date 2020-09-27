import datetime

import flask
import pytz

import config
import utils


app = flask.Flask(__name__)


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
        from_timestamp, to_timestamp = parse_query_params(flask.request.args)
    except (ValueError, TypeError) as e:
        print(e)
        return '', 400

    queries = utils.get_db_queries()

    timespan = to_timestamp - from_timestamp
    if timespan.days > 0:
        rows = queries.get_sparse_readings(
            from_timestamp=from_timestamp.isoformat(),
            to_timestamp=to_timestamp.isoformat(),
            nth_mins=10,
        )
    else:
        rows = queries.get_readings(
            from_timestamp=from_timestamp.isoformat(),
            to_timestamp=to_timestamp.isoformat(),
        )

    return flask.jsonify([utils.hydrate_reading(r) for r in rows])


@app.route('/readings/latest')
def get_latest_reading():
    queries = utils.get_db_queries()
    row = queries.get_latest_reading()

    return flask.jsonify(utils.hydrate_reading(row))

if __name__ == '__main__':
    app.run(debug=True)
