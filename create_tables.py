"""Create the Sparkify staging and analytics tables in Redshift."""

import configparser
import psycopg2
from sql_queries import create_table_queries, drop_table_queries


def drop_tables(cur, conn):
    """Drop all staging and analytics tables, committing each statement."""
    for query in drop_table_queries:
        cur.execute(query)
        conn.commit()


def create_tables(cur, conn):
    """Create all staging and analytics tables, committing each statement."""
    for query in create_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    """Connect to Redshift, reset the project tables, and close the connection."""
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))

    try:
        with conn.cursor() as cur:
            drop_tables(cur, conn)
            create_tables(cur, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()