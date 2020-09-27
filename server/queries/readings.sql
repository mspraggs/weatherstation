-- :name create_reading :insert
insert into readings (timestamp, temperature, relative_humidity, air_pressure, altitude) values (:timestamp, :temperature, :relative_humidity, :air_pressure, :altitude)

-- :name get_readings :many
select * from readings where timestamp >= :from_timestamp and timestamp < :to_timestamp order by timestamp

-- :name get_sparse_readings :many
select * from readings where timestamp >= :from_timestamp and timestamp < :to_timestamp and cast(strftime('%s', strftime('%Y-%m-%dT%H:%M', timestamp)) as int) % (60 * :nth_mins) = 0 order by timestamp

-- :name get_latest_reading :one
select * from readings order by timestamp desc limit 1;
