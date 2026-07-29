from django.urls import path
from . import views


urlpatterns = [
    path('offer-dashboard/',views.offer_dashboard,name='offer_dashboard'),
    path("category/", views.category_offer_list, name="category_offer_list"),
    path("category/add/", views.add_category_offer, name="add_category_offer"),
    path("category/edit/<uuid:offer_uuid>/",views.edit_category_offer,name="edit_category_offer"),
    path("category/delete/<uuid:offer_uuid>/",views.delete_category_offer,name='delete_category_offer'),
    path("product/", views.product_offer_list, name="product_offer_list"),
    path("product/add/", views.add_product_offer, name="add_product_offer"),
    path("product/edit/<uuid:offer_uuid>/",views.edit_product_offer,name="edit_product_offer"),
    path("product/delete/<uuid:offer_uuid>/",views.delete_product_offer,name="delete_product_offer"),
]
