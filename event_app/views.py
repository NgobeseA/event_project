from django.shortcuts import render,redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .forms import UserRegistrationForm, AdminUserCreationForm

# Create your views here.
def admin_dashboard(request):
    return render(request, 'adminDashboard.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, login)
            return redirect('home')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration.html', {'form': form})

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

@login_required
@user_passes_test(is_admin)
def admin_create_user(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'User {username} created successfully!')
            return redirect('admin_create_user')
    else:
        form = AdminUserCreationForm()
    return render(request, 'create_user.html', {'form': form})