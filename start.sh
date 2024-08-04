#!/bin/bash

python3 koop_form/manage.py migrate
python3 koop_form/manage.py crontab add
cron
pipenv run gunicorn --chdir ./koop_form config.wsgi:application --bind 0.0.0.0:8000