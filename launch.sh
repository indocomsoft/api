#!/usr/bin/env bash
if [ "$NO_POETRY" = "1" ]; then
  python src/app.py
else
  poetry run python src/app.py
fi
