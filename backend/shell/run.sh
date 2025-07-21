#!/bin/bash

cleanup() {
    echo "Cleaning up processes..."
    if [ ! -z "$CELERY_PID" ] && kill -0 $CELERY_PID 2>/dev/null; then
        echo "Stopping Celery worker (PID: $CELERY_PID)..."
        kill -TERM $CELERY_PID
    fi
    if [ ! -z "$DJANGO_PID" ] && kill -0 $DJANGO_PID 2>/dev/null; then
        echo "Stopping Django server (PID: $DJANGO_PID)..."
        kill -TERM $DJANGO_PID
    fi
    echo "Cleanup complete"
}

trap cleanup SIGINT SIGTERM EXIT

if [ "$USE_CELERY" = "False" ]; then
    echo "Celery is disabled, starting Django server only..."
    python manage.py runserver 0.0.0.0:8005
else
    echo "Starting Celery worker..."
    celery -A backend worker -l info --concurrency=1 &
    CELERY_PID=$!
    
    echo "Waiting for Celery to start (PID: $CELERY_PID)..."
    sleep 5
    
    if kill -0 $CELERY_PID 2>/dev/null; then
        echo "Celery worker started successfully"
    else
        echo "Warning: Celery worker failed to start, please check logs"
    fi
    
    echo "Starting Django server..."
    python manage.py runserver 0.0.0.0:8005 &
    DJANGO_PID=$!
    
    wait $DJANGO_PID $CELERY_PID
fi
