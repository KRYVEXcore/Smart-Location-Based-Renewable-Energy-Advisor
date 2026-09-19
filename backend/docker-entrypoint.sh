#!/bin/sh
set -e

# Idempotent: alembic tracks the applied revision in alembic_version, so
# re-running this on every container start (including Codespaces rebuilds)
# is a safe no-op once the database is already at head.
python -m alembic upgrade head

# Opt-in (RUN_DATA_SEED=true): loads the verified DISCOM/tariff/incentive data
# from app/data/. Validated first and idempotent (upsert, never deletes), so
# running it on every start is a safe no-op once the data is current. It logs
# the target database (password hidden) so the operator can confirm it.
# SEED_EXPECT_DATABASE, if set, aborts the seed unless the database name matches.
if [ "$RUN_DATA_SEED" = "true" ]; then
  if [ -n "$SEED_EXPECT_DATABASE" ]; then
    python -m scripts.seed_all --expect-database "$SEED_EXPECT_DATABASE"
  else
    python -m scripts.seed_all
  fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
