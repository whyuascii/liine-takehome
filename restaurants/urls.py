from django.urls import path
from restaurants.views import open_restaurants

urlpatterns = [
    path("restaurants/open/", open_restaurants, name="open-restaurants"),
]
