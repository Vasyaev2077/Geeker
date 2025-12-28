from django.urls import path
from . import views

app_name = "communities"

urlpatterns = [
    path("", views.CommunityListView.as_view(), name="community_list"),
    path("<slug:slug>/", views.CommunityDetailView.as_view(), name="community_detail"),
]








