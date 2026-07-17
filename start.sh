#!/bin/bash

rm -rf /app/koop_form/staticfiles/*
python koop_form/manage.py collectstatic --no-input

python3 koop_form/manage.py crontab add
cron
pipenv run gunicorn --chdir ./koop_form config.wsgi:application --bind 0.0.0.0:8000
