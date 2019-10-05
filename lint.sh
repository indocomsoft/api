#!/usr/bin/env bash
set -e

poetry run black --check .
poetry run isort --recursive --diff --check-only
poetry export -f requirements.txt | diff requirements.txt -
