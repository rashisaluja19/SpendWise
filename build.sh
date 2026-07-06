#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Force create or update the rashi superuser account on the live server
python -c "
import django
django.setup()
from django.contrib.auth.models import User
username = 'rashi'
email = ' '
password = '12345@#$'
user, created = User.objects.get_or_create(username=username)
user.email = email
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.save()
print('Live administrator account sync completed successfully!')
"