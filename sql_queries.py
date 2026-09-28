"""SQL statements for staging and the Sparkify song-play star schema."""

import configparser

# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')


def config_value(section, option, fallback):
    """Return a configured value without optional surrounding quote marks.

    Use ``fallback`` when the option is absent from the project configuration.
    """
    return config.get(section, option, fallback=fallback).strip("'\"")

# DROP TABLES
# Drop staging first and the fact table before its dimensions.
staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = 'DROP TABLE IF EXISTS "time"'

# STAGING TABLES
staging_events_table_create = """
CREATE TABLE staging_events (
    artist VARCHAR(512),
    auth VARCHAR(32),
    firstName VARCHAR(128),
    gender CHAR(1),
    itemInSession INTEGER,
    lastName VARCHAR(128),
    length DOUBLE PRECISION,
    level VARCHAR(32),
    location VARCHAR(1024),
    method VARCHAR(16),
    page VARCHAR(64),
    registration DOUBLE PRECISION,
    sessionId BIGINT,
    song VARCHAR(512),
    status INTEGER,
    ts BIGINT,
    userAgent VARCHAR(2048),
    userId BIGINT
)
"""

staging_songs_table_create = """
CREATE TABLE staging_songs (
    num_songs INTEGER,
    artist_id VARCHAR(256),
    artist_latitude DOUBLE PRECISION,
    artist_longitude DOUBLE PRECISION,
    artist_location VARCHAR(1024),
    artist_name VARCHAR(512),
    song_id VARCHAR(256),
    title VARCHAR(512),
    duration DOUBLE PRECISION,
    year INTEGER
)
"""

# FINAL TABLES

songplay_table_create = """
CREATE TABLE songplays (
    songplay_id BIGINT IDENTITY(0,1),
    start_time TIMESTAMP NOT NULL,
    user_id BIGINT,
    level VARCHAR(256),
    song_id VARCHAR(256),
    artist_id VARCHAR(256),
    session_id BIGINT,
    location VARCHAR(1024),
    user_agent VARCHAR(2048)
)
DISTKEY(user_id)
SORTKEY(start_time)
"""

user_table_create = """
CREATE TABLE users (
    user_id BIGINT NOT NULL,
    first_name VARCHAR(256),
    last_name VARCHAR(256),
    gender CHAR(1),
    level VARCHAR(256)
)
DISTKEY(user_id)
SORTKEY(user_id)
"""

song_table_create = """
CREATE TABLE songs (
    song_id VARCHAR(256) NOT NULL,
    title VARCHAR(512),
    artist_id VARCHAR(256),
    year INTEGER,
    duration DOUBLE PRECISION
)
DISTSTYLE ALL
SORTKEY(song_id)
"""

artist_table_create = """
CREATE TABLE artists (
    artist_id VARCHAR(256) NOT NULL,
    name VARCHAR(512),
    location VARCHAR(1024),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
)
DISTSTYLE ALL
SORTKEY(artist_id)
"""

time_table_create = """
CREATE TABLE "time" (
    start_time TIMESTAMP NOT NULL,
    hour SMALLINT,
    day SMALLINT,
    week SMALLINT,
    month SMALLINT,
    year SMALLINT,
    weekday SMALLINT
)
DISTSTYLE ALL
SORTKEY(start_time)
"""

staging_events_copy = """
COPY staging_events
FROM '{}'
IAM_ROLE '{}'
REGION 'us-west-2'
JSON '{}'
TIMEFORMAT 'epochmillisecs'
TRUNCATECOLUMNS BLANKSASNULL EMPTYASNULL
""".format(
    config_value("S3", "LOG_DATA", "s3://udacity-dend/log_data"),
    config.get("IAM_ROLE", "ARN", fallback="").strip("'\""),
    config_value("S3", "LOG_JSONPATH", "s3://udacity-dend/log_json_path.json"),
)

staging_songs_copy = """
COPY staging_songs
FROM '{}'
IAM_ROLE '{}'
REGION 'us-west-2'
JSON 'auto ignorecase'
TRUNCATECOLUMNS BLANKSASNULL EMPTYASNULL
""".format(
    config_value("S3", "SONG_DATA", "s3://udacity-dend/song_data"),
    config.get("IAM_ROLE", "ARN", fallback="").strip("'\""),
)

songplay_table_insert = """
INSERT INTO songplays (
    start_time, user_id, level, song_id, artist_id, session_id, location, user_agent
)
SELECT DISTINCT
    TIMESTAMP 'epoch' + e.ts / 1000.0 * INTERVAL '1 second',
    e.userId,
    e.level,
    s.song_id,
    s.artist_id,
    e.sessionId,
    e.location,
    e.userAgent
FROM staging_events e
LEFT JOIN staging_songs s
    ON e.song = s.title
    AND e.artist = s.artist_name
    AND e.length = s.duration
WHERE e.page = 'NextSong'
"""

user_table_insert = """
INSERT INTO users (user_id, first_name, last_name, gender, level)
SELECT user_id, first_name, last_name, gender, level
FROM (
    SELECT
        userId AS user_id,
        firstName AS first_name,
        lastName AS last_name,
        gender,
        level,
        ROW_NUMBER() OVER (PARTITION BY userId ORDER BY ts DESC) AS row_num
    FROM staging_events
    WHERE userId IS NOT NULL
) latest_users
WHERE row_num = 1
"""

song_table_insert = """
INSERT INTO songs (song_id, title, artist_id, year, duration)
SELECT song_id, title, artist_id, year, duration
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY song_id ORDER BY title) AS row_num
    FROM staging_songs
    WHERE song_id IS NOT NULL
) unique_songs
WHERE row_num = 1
"""

artist_table_insert = """
INSERT INTO artists (artist_id, name, location, latitude, longitude)
SELECT artist_id, artist_name, artist_location, artist_latitude, artist_longitude
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY artist_id ORDER BY artist_name) AS row_num
    FROM staging_songs
    WHERE artist_id IS NOT NULL
) unique_artists
WHERE row_num = 1
"""

time_table_insert = """
INSERT INTO "time" (start_time, hour, day, week, month, year, weekday)
SELECT DISTINCT
    start_time,
    EXTRACT(hour FROM start_time),
    EXTRACT(day FROM start_time),
    EXTRACT(week FROM start_time),
    EXTRACT(month FROM start_time),
    EXTRACT(year FROM start_time),
    EXTRACT(dow FROM start_time)
FROM songplays
"""

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
