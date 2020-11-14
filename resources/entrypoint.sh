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

echo "Starting daphne server."
daphne -b 0.0.0.0 \
    -p 8000 \
    games.asgi:application
