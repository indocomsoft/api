#!/usr/bin/env bash
env PYTHONPATH=src poetry run alembic upgrade head

if [ "$NO_POETRY" = "1" ]; then
  env PYTHONPATH=src alembic upgrade head
else
  env PYTHONPATH=src poetry run alembic upgrade head
fi
