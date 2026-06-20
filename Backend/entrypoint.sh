#!/bin/bash
set -e
python manage.py migrate --noinput
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 backend_project.wsgi:application
