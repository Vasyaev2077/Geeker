from django.urls import path
<<<<<<< HEAD
from django.views.generic import RedirectView
=======
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753
from . import views

app_name = "library"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
<<<<<<< HEAD
    path("collections/", RedirectView.as_view(pattern_name="library:home", permanent=False), name="collection_list"),
=======
    path("collections/", views.CollectionListView.as_view(), name="collection_list"),
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753
    path("collections/create/", views.CollectionCreateView.as_view(), name="collection_create"),
    path("collections/<int:pk>/", views.CollectionDetailView.as_view(), name="collection_detail"),
    path("collections/<int:pk>/edit/", views.CollectionUpdateView.as_view(), name="collection_edit"),
    path("collections/<int:pk>/delete/", views.CollectionDeleteView.as_view(), name="collection_delete"),
    path("sections/create/", views.SectionCreateView.as_view(), name="section_create"),
<<<<<<< HEAD
    path("sections/<int:pk>/", views.SectionDetailView.as_view(), name="section_detail"),
    path("sections/<int:pk>/edit/", views.SectionUpdateView.as_view(), name="section_edit"),
    path("sections/<int:pk>/delete/", views.SectionDeleteView.as_view(), name="section_delete"),
    path("items/add/", views.ItemCreateView.as_view(), name="item_create"),
    path("sections/<int:pk>/items/add/", views.SectionItemCreateView.as_view(), name="section_item_create"),
    path("items/<int:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("items/<int:pk>/edit/", views.ItemUpdateView.as_view(), name="item_edit"),
    path("items/<int:pk>/delete/", views.ItemDeleteView.as_view(), name="item_delete"),
    path("items/<int:pk>/move/", views.ItemMoveToSectionView.as_view(), name="item_move"),
    path("api/barcode-lookup/", views.BarcodeLookupView.as_view(), name="barcode_lookup"),
    path("api/fetch-image/", views.FetchImageView.as_view(), name="fetch_image"),
=======
    path("sections/<int:pk>/edit/", views.SectionUpdateView.as_view(), name="section_edit"),
    path("sections/<int:pk>/delete/", views.SectionDeleteView.as_view(), name="section_delete"),
    path("items/add/", views.ItemCreateView.as_view(), name="item_create"),
    path("items/<int:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("items/<int:pk>/edit/", views.ItemUpdateView.as_view(), name="item_edit"),
    path("items/<int:pk>/delete/", views.ItemDeleteView.as_view(), name="item_delete"),
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753
]







