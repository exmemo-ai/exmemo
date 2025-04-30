#!/bin/bash

cd backend

if [ "$USE_CELERY" = "False" ]; then
    python manage.py runserver 0.0.0.0:8005
else
    celery -A backend worker -l info &
    python manage.py runserver 0.0.0.0:8005
fi
