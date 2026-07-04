from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.home_page,name='home'),
    path('user-products/',views.user_product_list,name='user_product_list'),
    path('user-products/category/<int:category_id>/',views.user_product_list,name='user_product_by_category'),
    path('user-product-details/<int:pk>/',views.user_product_details,name='user_product_details'),
    path('product-unavailable/',views.product_unavailable,name='product_unavailable'),
       
]

