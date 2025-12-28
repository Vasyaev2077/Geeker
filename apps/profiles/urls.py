from django.urls import path
from . import views

app_name = "profiles"

urlpatterns = [
    path("", views.ProfileDetailView.as_view(), name="detail"),
    path("edit/", views.ProfileUpdateView.as_view(), name="edit"),
    path("settings/", views.ProfileSettingsView.as_view(), name="settings"),
]







