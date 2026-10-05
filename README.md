# Data Warehouse (Udacity Data Engineer Nanodegree)

## Purpose

Sparkify wants to understand which songs listeners play and how listening varies by user, subscription level, location, and time. This project loads the supplied song metadata and streaming activity logs into Amazon Redshift and organizes them for song-play analysis.

## Schema design

The warehouse uses a star schema centered on `songplays`, with `users`, `songs`, `artists`, and `time` as dimensions. Each fact row represents a log event whose page is `NextSong`. Its timestamp, user, session, subscription level, location, and user agent support behavioral analysis; song and artist IDs are populated by matching the event's song title, artist, and duration to the catalog.

The dimensions keep descriptive attributes out of the fact table and make common analytical joins straightforward. The fact table is distributed by user and sorted by play time. Small song, artist, and time dimensions use `DISTSTYLE ALL` to avoid redistribution during joins. The user dimension is distributed by user ID. Redshift does not enforce primary or foreign key constraints, so the schema uses stable source IDs and deduplicates dimension records during insertion. The generated `songplay_id` uses Redshift's `IDENTITY(0,1)` syntax.

## ETL pipeline

1. `create_tables.py` drops any prior staging and analytics tables, then creates them in dependency order. The script is safe to run again to reset the warehouse.
2. `etl.py` truncates the prior run's staging and analytics data, then uses Redshift `COPY` to load JSON song files and event logs from S3 into staging tables. The log COPY command uses the provided JSONPaths file. The SQL uses the S3 paths in `dwh.cfg`.
3. Insert statements populate the dimensions and song-play fact table. User rows use the latest event per user to retain the current subscription level. Song and artist rows are deduplicated by their source IDs. Event timestamps are in epoch milliseconds and are converted to Redshift timestamps; the time dimension extracts hour, day, week, month, year, and weekday.

Run from this directory after configuring the cluster and IAM role:

```bash
python create_tables.py
python etl.py
```

## Configuration and access

Fill in `HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `DB_PORT` in the `[CLUSTER]` section of `dwh.cfg`. Set `[IAM_ROLE] ARN` to the ARN of a Redshift IAM role that can read the specified S3 objects. The file contains blank cluster fields because credentials and cluster details are environment-specific; no AWS resources are created by these scripts.

The configured sources are `s3://udacity-dend/song_data`, `s3://udacity-dend/log_data`, and `s3://udacity-dend/log_json_path.json`.

## Run locally with Docker Compose

Redshift is an AWS service, so Compose runs a PostgreSQL-compatible local version of the warehouse instead. The local runner reads the same public S3 JSON datasets anonymously, creates equivalent tables in PostgreSQL, and executes the same analytics inserts. The Redshift scripts above remain the path for an actual Redshift cluster.

Requirements: Docker with the Compose plugin, network access to Docker Hub and the public S3 bucket, and enough disk space for the downloaded datasets and PostgreSQL volume.

```bash
docker compose up -d warehouse
docker compose run --build --rm etl
```

The ETL container exits after loading the data; PostgreSQL remains available on `localhost:5432` with database/user/password `sparkify`. For example, connect with `psql -h localhost -U sparkify -d sparkify`, then query `songplays` or join to the dimensions. The local runner recreates its tables on each run, so rerunning it replaces the previous dataset. Start it again with:

```bash
docker compose run --rm etl
```

Stop the database with `docker compose down`. Remove its persisted data as well with `docker compose down -v`.

## Example analysis queries

Plays by song:

```sql
SELECT s.title, COUNT(*) AS plays
FROM songplays sp
JOIN songs s ON sp.song_id = s.song_id
GROUP BY s.title
ORDER BY plays DESC
LIMIT 10;
```

Plays by hour of day:

```sql
SELECT t.hour, COUNT(*) AS plays
FROM songplays sp
JOIN "time" t ON sp.start_time = t.start_time
GROUP BY t.hour
ORDER BY t.hour;
```
