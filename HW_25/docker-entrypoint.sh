python manage.py collectstatic --noinput
python manage.py migrate
exec gunicorn book_store.wsgi:application --bind 0.0.0.0:8000