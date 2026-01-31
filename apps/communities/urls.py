from django.urls import path
from . import views

app_name = "communities"

urlpatterns = [
    path("", views.CommunityListView.as_view(), name="community_list"),
    path("<slug:slug>/join/", views.CommunityJoinToggleView.as_view(), name="community_join_toggle"),
    path("<slug:slug>/", views.CommunityDetailView.as_view(), name="community_detail"),
]








