#!/usr/bin/env bash
poetry run black .
poetry run isort -y
poetry export -f requirements.txt > requirements.txt
