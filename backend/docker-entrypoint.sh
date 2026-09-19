#!/bin/sh
set -e

# Idempotent: alembic tracks the applied revision in alembic_version, so
# re-running this on every container start (including Codespaces rebuilds)
# is a safe no-op once the database is already at head.
python -m alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
