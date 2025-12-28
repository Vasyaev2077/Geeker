from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("collections/", views.CollectionListView.as_view(), name="collection_list"),
    path("collections/create/", views.CollectionCreateView.as_view(), name="collection_create"),
    path("collections/<int:pk>/", views.CollectionDetailView.as_view(), name="collection_detail"),
    path("collections/<int:pk>/edit/", views.CollectionUpdateView.as_view(), name="collection_edit"),
    path("collections/<int:pk>/delete/", views.CollectionDeleteView.as_view(), name="collection_delete"),
    path("sections/create/", views.SectionCreateView.as_view(), name="section_create"),
    path("sections/<int:pk>/edit/", views.SectionUpdateView.as_view(), name="section_edit"),
    path("sections/<int:pk>/delete/", views.SectionDeleteView.as_view(), name="section_delete"),
    path("items/add/", views.ItemCreateView.as_view(), name="item_create"),
    path("items/<int:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("items/<int:pk>/edit/", views.ItemUpdateView.as_view(), name="item_edit"),
    path("items/<int:pk>/delete/", views.ItemDeleteView.as_view(), name="item_delete"),
]







