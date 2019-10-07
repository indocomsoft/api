#!/usr/bin/env bash
set -e

poetry run black --check .
poetry run isort --recursive --diff --check-only

mv requirements.txt requirements2.txt
poetry export -f requirements.txt
diff requirements.txt requirements2.txt || (mv requirements2.txt requirements.txt; false)
mv requirements2.txt requirements.txt
