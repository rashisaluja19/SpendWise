#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Force Django to know where your settings file is, then fix rashi's password
export DJANGO_SETTINGS_MODULE="cute_expense_tracker.settings"
python -c "
import django
django.setup()
from django.contrib.auth.models import User
try:
    user = User.objects.get(username='rashi')
    user.set_password('12345@#$')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print('Password successfully updated for existing rashi account!')
except User.DoesNotExist:
    User.objects.create_superuser('rashi', 'rashi@spendwise.local', '12345@#$')
    print('Created brand new rashi superuser account!')
"