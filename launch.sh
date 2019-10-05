#!/usr/bin/env bash
if [ "$NO_POETRY" = "1" ]; then
  python src/main.py
else
  poetry run python src/main.py
fi
