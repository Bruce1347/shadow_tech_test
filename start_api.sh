#!/bin/bash

# Create missing database tables
PYTHONPATH=/home/app /home/app/.local/bin/poetry run python /home/app/src/bootstrap_database_schema.py

# Start the API
/home/app/.local/bin/poetry run uvicorn --host 0.0.0.0 src.api.main:app
