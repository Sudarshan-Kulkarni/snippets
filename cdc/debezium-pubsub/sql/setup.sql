-- Demo table for CDC.
CREATE TABLE IF NOT EXISTS public.customers (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- FULL makes UPDATE/DELETE events include the complete "before" row.
-- (The default only includes the primary key.)
ALTER TABLE public.customers REPLICA IDENTITY FULL;

-- Publication: which tables are exposed to logical replication.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'dbz_publication') THEN
        CREATE PUBLICATION dbz_publication FOR TABLE public.customers;
    END IF;
END
$$;
