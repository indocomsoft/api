# Acquity: Back-End

## Setup
Install pip3
```
sudo apt install python3-pip
```
Install Poetry (https://poetry.eustace.io), prerelease version
```
curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | env POETRY_PREVIEW=1 python
```
Install dependencies
```
poetry install
```
Setup/reset database (install Postgres first)
```
./setup_db.sh
```

## Run app
```
env ACQUITY_ENV=DEVELOPMENT ./launch.sh
```

## Lint
Auto-fix: `./lint_fix.sh`

Check (is run in CI): `./lint.sh`

## Database migrations
Generate migrations: `./generate_migration.sh "Change foo"`

Run migrations: `./run_migrations.sh`
