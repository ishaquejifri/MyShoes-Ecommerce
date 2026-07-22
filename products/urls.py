from django.urls import path
from . import views


app_name = 'products'

urlpatterns = [
    path('product/',views.product_list,name='product_list'),
    path('add-product/',views.add_product,name='add_product'),
    path('edit-product/<uuid:product_uuid>/',views.edit_product,name='edit_product'),
    path('product-details/<uuid:product_uuid>/',views.product_details,name='product_details'),
    path('add-variant/<uuid:product_uuid>/',views.add_variant,name='add_variant'),
    path('variant/edit/<uuid:variant_uuid>/',views.edit_variant,name='edit_variant'),
    path('variant/delete/<uuid:variant_uuid>/',views.delete_variant,name='delete_variant'),
    path('delete-product/<uuid:product_uuid>/',views.delete_product,name='delete_product'),
    path('toggle-listing/<uuid:product_uuid>/',views.toggle_listing,name='toggle_listing'),
    
]

   