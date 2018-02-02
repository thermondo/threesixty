release: python manage.py migrate --no-input
web: waitress-serve --port=${PORT:-5000} --threads=${WEB_CONCURRENCY:-4} threesixty.wsgi:application
