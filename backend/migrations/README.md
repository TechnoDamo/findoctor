# Alembic Migrations

This directory contains schema migrations for the backend PostgreSQL database.

Use the documented commands from `backend/Makefile`:

```bash
cd backend
make db-up
make migrate
make migration m="describe change"
make rollback
make db-current
make db-history
```

Application query SQL should live under `backend/app/db/queries/`, not in migration files.
