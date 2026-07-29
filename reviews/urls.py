from django.urls import path
from . import views

urlpatterns = [
    path("add/<uuid:product_uuid>/", views.add_review, name="add_review"),
]