from django.contrib import admin
from .models import UserProfile, Expense

admin.site.register(UserProfile)
admin.site.register(Expense)