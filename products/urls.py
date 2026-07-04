from django.urls import path
from . import views


app_name = 'products'

urlpatterns = [
    path('product/',views.product_list,name='product_list'),
    path('add-product/',views.add_product,name='add_product'),
    path('edit-product/<int:id>/',views.edit_product,name='edit_product'),
    path('product-details/<int:id>',views.product_details,name='product_details'),
    path('add-variant/<int:product_id>',views.add_variant,name='add_variant'),
    path('variant/edit/<int:variant_id>/',views.edit_variant,name='edit_variant'),
    path('variant/delete/<int:variant_id>/',views.delete_variant,name='delete_variant'),
    path('delete-product/<int:id>',views.delete_product,name='delete_product'),
    path('toggle-listing/<int:id>/',views.toggle_listing,name='toggle_listing'),
    
]

   