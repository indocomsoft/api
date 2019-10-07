#!/usr/bin/env bash
sudo -u postgres psql -c "DROP DATABASE acquity"
sudo -u postgres psql -c "DROP ROLE acquity"
sudo -u postgres psql -c "CREATE ROLE acquity WITH LOGIN PASSWORD 'acquity'"
sudo -u postgres psql -c "CREATE DATABASE acquity"
./run_migrations.sh
poetry run python src/seeds.py
