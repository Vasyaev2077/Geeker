from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, TemplateView
from django.urls import reverse_lazy
from .models import UserProfile
from .forms import UserProfileForm


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = "profiles/profile_detail.html"

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"display_name": self.request.user.username},
        )
        return profile


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "profiles/profile_form.html"
    success_url = reverse_lazy("profiles:detail")

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"display_name": self.request.user.username},
        )
        return profile


class ProfileSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "profiles/settings.html"






