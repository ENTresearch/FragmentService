#!/bin/bash

if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo ".env file not found!"
    exit 1
fi

attempt=1
max_attempts=30
until docker exec $(docker ps -qf "name=db") pg_isready -U ${POSTGRES_USER} || [ $attempt -eq $max_attempts ]
do
    echo "Waiting for database... (attempt $attempt)"
    sleep 2
    attempt=$((attempt + 1))
done

docker exec -i $(docker ps -qf "name=db") psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./src/sql/init.sql