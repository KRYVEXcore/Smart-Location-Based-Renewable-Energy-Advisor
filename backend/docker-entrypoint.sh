#!/bin/sh
set -e

# Idempotent: alembic tracks the applied revision in alembic_version, so
# re-running this on every container start (including Codespaces rebuilds)
# is a safe no-op once the database is already at head.
python -m alembic upgrade head

# Opt-in (RUN_DATA_SEED=true): loads the verified DISCOM/tariff/incentive data
# from app/data/. Validated first, idempotent (upsert, never deletes) and
# serialised by a Postgres advisory lock, so concurrent starts cannot create
# duplicates. It logs the target database (password hidden). -u keeps the
# output unbuffered so progress is visible in the deploy log.
# SEED_EXPECT_DATABASE, if set, aborts the seed unless the database name matches.
# A failed seed is logged loudly but does not stop the API: it then serves
# whatever data already exists (unconfigured states answer honestly).
if [ "$RUN_DATA_SEED" = "true" ]; then
  if [ -n "$SEED_EXPECT_DATABASE" ]; then
    python -u -m scripts.seed_all --expect-database "$SEED_EXPECT_DATABASE" || echo "DATA SEED FAILED: starting the API without new data" >&2
  else
    python -u -m scripts.seed_all || echo "DATA SEED FAILED: starting the API without new data" >&2
  fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
