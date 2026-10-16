"""Make an insert, an update and a delete on public.customers to generate CDC events."""
import time
import uuid

import psycopg2

from config import db_connect_kwargs


def main() -> None:
    """Run each statement in its own transaction so each produces a separate change event."""
    suffix = uuid.uuid4().hex[:6]
    conn = psycopg2.connect(**db_connect_kwargs())
    conn.autocommit = True  # one transaction per statement
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO public.customers (name, email) VALUES (%s, %s) RETURNING id",
            (f"Customer {suffix}", f"{suffix}@example.com"),
        )
        row_id = cur.fetchone()[0]
        print(f"INSERT id={row_id}")
        time.sleep(1)

        cur.execute(
            "UPDATE public.customers SET email = %s, updated_at = now() WHERE id = %s",
            (f"{suffix}.updated@example.com", row_id),
        )
        print(f"UPDATE id={row_id}")
        time.sleep(1)

        cur.execute("DELETE FROM public.customers WHERE id = %s", (row_id,))
        print(f"DELETE id={row_id}")
    conn.close()


if __name__ == "__main__":
    main()
