from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Expense, RecurringSubscription
from datetime import date, timedelta, datetime
import calendar
import json
from django.http import HttpResponse
from django.contrib.auth.models import User
import csv

def secret_admin_reset(request):
    # This will dynamically grab or fix the rashi account right inside the live web process
    user, created = User.objects.get_or_create(username='rashi')
    user.set_password('12345@#$')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    return HttpResponse("<h3>Admin account synchronized successfully! You can now close this tab.</h3>")

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
                # 🤖 SMART AUTO-CATEGORIZATION LOGIC
                # Title ko lowercase mein convert kar rahe hain matching ke liye
                check_text = title.lower()
                
                # Agar keywords match hote hain toh drop-down value ko overwrite kar do
                if any(keyword in check_text for keyword in ['uber', 'metro', 'petrol', 'auto', 'cab', 'ola', 'train']):
                    category = 'Travel'
                elif any(keyword in check_text for keyword in ['zomato', 'restaurant', 'maggi', 'swiggy', 'cafe', 'dinner', 'lunch', 'burger']):
                    category = 'Food'
                elif any(keyword in check_text for keyword in ['bill', 'electricity', 'wifi', 'rent', 'recharge']):
                    category = 'Bills'
                    
                # Logs it for the first day of the historical month if you are viewing the past,
                # or today's date if you are viewing the current month.
                if selected_month == today.month and selected_year == today.year:
                    log_date = today.date()
                else:
                    log_date = datetime(selected_year, selected_month, 1).date()
                    
                Expense.objects.create(
                    user=request.user,
                    title=title,
                    amount=amount,
                    category=category,  # Auto-assigned or manual category saved here
                    date=log_date,
                    is_automated=False
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
    category_totals = {'Food':0,'Travel': 0, 'Shopping': 0, 'Bills': 0, 'Entertainment': 0, 'Other': 0}
    for expense in all_expenses:
        if expense.category in category_totals:
            category_totals[expense.category] += float(expense.amount)
        elif expense.is_automated:
            category_totals['Bills'] += float(expense.amount)
        else:
            category_totals['Other'] += float(expense.amount)

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

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user)
    
    # 🔍 1. Category Filter Logic
    category_filter = request.GET.get('category')
    if category_filter:
        expenses = expenses.filter(category=category_filter)
        
    # 📅 2. Date Range Filter Logic (This Week / This Month)
    date_filter = request.GET.get('date_range')
    today = date.today()
    
    if date_filter == 'this_week':
        start_of_week = today - timedelta(days=today.weekday()) # Monday se start
        expenses = expenses.filter(date__range=[start_of_week, today])
    elif date_filter == 'this_month':
        expenses = expenses.filter(date__year=today.year, date__month=today.month)

    # Latest entries top par dikhane ke liye
    expenses = expenses.order_by('-date')
    
    # unique categories nikalne ke liye dropdown ke liye
    categories = ['Food', 'Travel', 'Bills', 'Others'] 
        
    context = {
        'expenses': expenses,
        'categories': categories,
        'selected_category': category_filter,
        'selected_date': date_filter,
    }
    return render(request, 'tracker/expenses.html', context)


@login_required
def export_expenses_csv(request):
    # Setup response metadata to trigger Excel/CSV file download
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{request.user.username}_expenses.csv"'
    
    writer = csv.writer(response)
    # Excel Sheets ke Table Columns Headers
    writer.writerow(['Title', 'Amount', 'Category', 'Date'])
    
    # Strict Isolation: Data matrix fetch for current user only
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    
    for expense in expenses:
        writer.writerow([expense.title, expense.amount, expense.category, expense.date])
        
    return response