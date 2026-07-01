from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    daily_travel_default = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    daily_food_default = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Travel', 'Travel (Auto)'),
        ('Food', 'Food (Auto)'),
        ('Shopping', 'Shopping'),
        ('Bills', 'Bills & Utilities'),
        ('Entertainment', 'Entertainment'),
        ('Other', 'Other Extra Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200) # Fixed
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES) # Fixed
    date = models.DateField()
    is_automated = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.user.username})"
    

class RecurringSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - ₹{self.cost}"