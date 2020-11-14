#!/usr/bin/env bash

set -e

until pg_isready --host="${POSTGRES_HOST}" --username="${POSTGRES_USER}" --quiet; do
    sleep 1;
done

touch -a /games/log/awsgi.log
touch -a /games/log/django.log

cd /games/src/website

./manage.py migrate --no-input

chown --recursive www-data:www-data /games/

echo "Starting uvicorn server."
uvicorn --root-path=/games/src/website \
    --port=:8000 \
    --processes=5 \
    --uid=www-data --gid=www-data \
    --limit-concurrency=5000 \
    games.asgi:application
