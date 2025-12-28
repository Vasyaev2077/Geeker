from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.ChatListView.as_view(), name="chat_list"),
    path("<int:pk>/", views.ChatDetailView.as_view(), name="chat_detail"),
]








