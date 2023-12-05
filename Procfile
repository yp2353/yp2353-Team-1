web: gunicorn --max-requests 100 --bind :8000 --workers 2 --threads 2 vibecheck.wsgi:application
websocket: daphne -b 0.0.0.0 -p 5000 vibecheck.asgi:application

