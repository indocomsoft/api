#!/usr/bin/env bash
env ACQUITY_ENV=TEST PYTHONPATH=. poetry run pytest --cov-report html --cov=src
