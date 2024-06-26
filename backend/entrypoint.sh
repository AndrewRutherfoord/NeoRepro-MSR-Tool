#!/usr/bin/env bash

# The starting point for the backend Docker container. This should only be called by the Dockerfile.
# It migrates the database and starts the applcation.

cd /app/backend/backend

# Migrate the database with Alembic
echo "Alembic Migrating Database..."
alembic upgrade head
echo "Database Migrated Successfully"

cd /app/backend

# Start the backend
echo "Starting the backend"
fastapi dev ./backend/main.py
