"""Run sql/setup.sql against Neon (creates the demo table and the publication)."""
from pathlib import Path

import psycopg2

from config import db_connect_kwargs


def main() -> None:
    sql = (Path(__file__).parent / "sql" / "setup.sql").read_text()
    with psycopg2.connect(**db_connect_kwargs()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("SHOW wal_level")
            wal_level = cur.fetchone()[0]
    print("Table and publication are ready.")
    print(f"wal_level = {wal_level}")
    if wal_level != "logical":
        print("WARNING: wal_level is not 'logical'. Enable logical replication in the Neon project settings.")


if __name__ == "__main__":
    main()
