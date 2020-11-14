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

echo "Starting asgi server."
asgi --chdir=/games/src/website \
    --module=games.asgi:application \
    --master --pidfile=/tmp/project-master.pid \
    --socket=:8000 \
    --processes=5 \
    --uid=www-data --gid=www-data \
    --harakiri=20 \
    --post-buffering=16384 \
    --max-requests=5000 \
    --thunder-lock \
    --vacuum \
    --logfile-chown \
    --logto2=/games/log/asgi.log \
    --ignore-sigpipe \
    --ignore-write-errors \
    --disable-write-exception
