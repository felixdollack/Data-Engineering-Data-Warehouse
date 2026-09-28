"""Load S3 data into Redshift staging tables and build analytics tables."""

import configparser
import psycopg2
from sql_queries import copy_table_queries, insert_table_queries


def load_staging_tables(cur, conn):
    """Run the S3 COPY statements that load events and songs into staging."""
    for query in copy_table_queries:
        cur.execute(query)
        conn.commit()


def insert_tables(cur, conn):
    """Transform staging data into songplays and its dimension tables."""
    for query in insert_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    """Run the full Redshift ETL sequence and always close the connection."""
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))

    try:
        with conn.cursor() as cur:
            load_staging_tables(cur, conn)
            insert_tables(cur, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()