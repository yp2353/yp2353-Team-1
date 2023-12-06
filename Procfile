web: gunicorn --bind :8000 --workers 2 --threads 2 vibecheck.wsgi:application --max-requests 2000
websocket: daphne -b 0.0.0.0 -p 5000 vibecheck.asgi:application