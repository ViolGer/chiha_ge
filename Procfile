release: python manage.py migrate && python manage.py load_vocab
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
