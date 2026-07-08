from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('export-csv/', views.export_expenses_csv, name='export_expenses_csv'),
    #path('secret-rashi-activation-gate-99/', views.secret_admin_reset, name='secret_admin_reset'),
]