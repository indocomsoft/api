#!/usr/bin/env bash
env PYTHONPATH=. poetry run alembic upgrade head

if [ "$NO_POETRY" = "1" ]; then
  env PYTHONPATH=. alembic upgrade head
else
  env PYTHONPATH=. poetry run alembic upgrade head
fi
