from django.urls import path
from .views import HomeMenuView

app_name = "core"

urlpatterns = [
    path("", HomeMenuView.as_view(), name="home"),
]




