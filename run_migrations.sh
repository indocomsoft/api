#!/usr/bin/env bash
env PYTHONPATH=src poetry run alembic upgrade head
