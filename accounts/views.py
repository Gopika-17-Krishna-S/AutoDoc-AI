from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.views import View

class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        form = UserCreationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
        return render(request, 'accounts/register.html', {'form': form})

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get('next', '/'))
        return render(request, 'accounts/login.html', {'form': form})

class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('/auth/login/')
