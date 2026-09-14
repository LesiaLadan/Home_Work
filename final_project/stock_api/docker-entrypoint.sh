python manage.py collectstatic --noinput
python manage.py migrate
exec gunicorn stock_service.wsgi:application --bind 0.0.0.0:8000
