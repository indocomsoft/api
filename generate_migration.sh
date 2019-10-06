#!/usr/bin/env bash
if [ "$#" -ne 1 ]; then
  echo "Please specify message"
  echo "e.g. $0 'Change foo'"
  exit 1
fi

if [ "$NO_POETRY" = "1" ]; then
  env PYTHONPATH=src alembic revision --autogenerate -m "$1"
else
  env PYTHONPATH=src poetry run alembic revision --autogenerate -m "$1"
fi
