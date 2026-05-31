"""Create a clean PostgreSQL test database for the backend test suite."""

from __future__ import annotations

import os

import psycopg
from psycopg import sql


def main() -> None:
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5433")
    user = os.environ.get("POSTGRES_USER", "findoctor")
    password = os.environ.get("POSTGRES_PASSWORD", "change_me")
    test_db = os.environ.get("TEST_POSTGRES_DB", "findoctor_test")

    dsn = f"postgres://{user}:{password}@{host}:{port}/postgres"
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
            """,
            (test_db,),
        )
        conn.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(test_db)))
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_db)))

    print(f"Test database reset: {test_db}")


if __name__ == "__main__":
    main()
