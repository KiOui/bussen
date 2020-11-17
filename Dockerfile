FROM python:3.8
MAINTAINER Lars van Rhijn

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE games.settings.production
ENV PATH /root/.poetry/bin:${PATH}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /games/src
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY poetry.lock pyproject.toml /games/src/

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends postgresql-client cron && \
    rm --recursive --force /var/lib/apt/lists/* && \
    \
    mkdir --parents /games/src/ && \
    mkdir --parents /games/log/ && \
    mkdir --parents /games/static/ && \
    chmod +x /usr/local/bin/entrypoint.sh && \
    \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python && \
    poetry config --no-interaction --no-ansi virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-dev


COPY website /games/src/website/

RUN echo "0 0 * * * www-data /games/src/website/manage.py dataminimisation" >> /etc/crontab
RUN service cron start
