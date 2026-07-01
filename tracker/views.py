from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Expense, RecurringSubscription
from datetime import datetime
import calendar
import json

@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    today = datetime.today()
    
    # 📅 Get selected month and year from the GET request parameters (defaults to current month)
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    
    # Handle Form Actions
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile.monthly_salary = request.POST.get('monthly_salary', 0)
            profile.daily_travel_default = request.POST.get('daily_travel_default', 0)
            profile.daily_food_default = request.POST.get('daily_food_default', 0)
            profile.save()
            return redirect(f'/?month={selected_month}&year={selected_year}')
            
        elif 'add_expense' in request.POST:
            title = request.POST.get('title')
            amount = request.POST.get('amount')
            category = request.POST.get('category')
            if title and amount and category:
                # Logs it for the first day of the historical month if you are viewing the past, 
                # or today's date if you are viewing the current month.
                log_date = today.date() if (selected_month == today.month and selected_year == today.year) else datetime(selected_year, selected_month, 1).date()
                Expense.objects.create(
                    user=request.user, title=title, amount=amount,
                    category=category, date=log_date, is_automated=False
                )
                return redirect(f'/?month={selected_month}&year={selected_year}')
                
        elif 'approve_subscription' in request.POST:
            sub_title = request.POST.get('sub_title')
            sub_amount = request.POST.get('sub_amount')
            log_date = today.date() if (selected_month == today.month and selected_year == today.year) else datetime(selected_year, selected_month, 1).date()
            Expense.objects.create(
                user=request.user, title=f"Approved Sub: {sub_title}", amount=sub_amount,
                category='Bills', date=log_date, is_automated=True
            )
            return redirect(f'/?month={selected_month}&year={selected_year}')

        elif 'add_subscription_target' in request.POST:
            sub_name = request.POST.get('new_sub_name')
            sub_cost = request.POST.get('new_sub_cost')
            if sub_name and sub_cost:
                RecurringSubscription.objects.create(user=request.user, name=sub_name, cost=sub_cost)
                return redirect(f'/?month={selected_month}&year={selected_year}')

    # Core Calculations based on Selected Month/Year
    total_days = calendar.monthrange(selected_year, selected_month)[1]
    auto_travel_total = profile.daily_travel_default * total_days
    auto_food_total = profile.daily_food_default * total_days
    total_fixed_expenses = auto_travel_total + auto_food_total
    
    # Filter expenses for the SELECTED timeline window
    all_expenses = Expense.objects.filter(
        user=request.user, date__year=selected_year, date__month=selected_month
    ).order_by('-id')
    
    total_logged_expenses = sum(expense.amount for expense in all_expenses)
    net_savings = profile.monthly_salary - (total_fixed_expenses + total_logged_expenses)

    # Dynamic Subscription Scanner Engine
    user_subs = RecurringSubscription.objects.filter(user=request.user)
    pending_sub = None
    for sub in user_subs:
        already_logged = all_expenses.filter(title=f"Approved Sub: {sub.name}").exists()
        if not already_logged:
            pending_sub = sub
            break

    # Chart Processing
    category_totals = {'Shopping': 0, 'Bills': 0, 'Entertainment': 0, 'Other': 0}
    for expense in all_expenses:
        if expense.category in category_totals:
            category_totals[expense.category] += float(expense.amount)
        elif expense.is_automated:
            category_totals['Bills'] += float(expense.amount)

    chart_labels = list(category_totals.keys())
    chart_values = list(category_totals.values())
    
    # Build a simple list of recent months for our dropdown menu
    view_month_name = datetime(selected_year, selected_month, 1).strftime('%B %Y')
    
    context = {
        'profile': profile,
        'total_days': total_days,
        'auto_travel_total': auto_travel_total,
        'auto_food_total': auto_food_total,
        'total_fixed_expenses': total_fixed_expenses,
        'manual_expenses': all_expenses,
        'net_savings': net_savings,
        'current_month': view_month_name,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'pending_sub': pending_sub,
    }
    return render(request, 'tracker/dashboard.html', context)

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log the user in after signing up
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')