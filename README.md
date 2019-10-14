# Acquity: Back-End

## Setup
Install Python 3.7. Use `pyenv` (https://github.com/pyenv/pyenv) to make life easy
```
curl https://pyenv.run | bash
pyenv install 3.7
pyenv local 3.7
```
Install Poetry (https://poetry.eustace.io), version 1.0.0a5
```
curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | env POETRY_VERSION=1.0.0a5 python
```
Install dependencies
```
poetry install
```
Setup/reset database (install Postgres first)
```
./setup_db.sh
```
Add the environmental variables CLIENT_ID and CLIENT_SECRET
```
cp .env.default .env
```
## Run app
```
env ACQUITY_ENV=DEVELOPMENT ./launch.sh
```

## Test
```
./test.sh
```

## Lint
Auto-fix: `./lint_fix.sh`

Check (is run in CI): `./lint.sh`

## Database migrations
Generate migrations: `./generate_migration.sh "Change foo"`

Run migrations: `env ACQUITY_ENV=DEVELOPMENT ./run_migrations.sh`
