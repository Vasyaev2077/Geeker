from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from .forms import LocalUserCreationForm


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        form = AuthenticationForm(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("library:home")
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("accounts:login")


class RegisterView(View):
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def get(self, request):
        form = LocalUserCreationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LocalUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        return render(request, self.template_name, {"form": form})








