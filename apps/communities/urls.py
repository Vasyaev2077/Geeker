from django.urls import path
from . import views

app_name = "communities"

urlpatterns = [
    path("", views.CommunityListView.as_view(), name="community_list"),
<<<<<<< HEAD
    path("<slug:slug>/join/", views.CommunityJoinToggleView.as_view(), name="community_join_toggle"),
=======
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753
    path("<slug:slug>/", views.CommunityDetailView.as_view(), name="community_detail"),
]








