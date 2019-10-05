#!/usr/bin/env bash
env PYTHONPATH=. poetry run alembic upgrade head
