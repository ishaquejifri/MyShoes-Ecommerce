from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    
    path('add/<int:product_id>/',views.add_to_cart,name='add_to_cart'),
    path('',views.view_cart,name='view_cart'),
    path('update/<int:item_id>/<str:action>/',views.update_cart,name='update_cart'),
    path('remove/<int:item_id>/',views.remove_from_cart,name='remove_from_cart'),
    path('ajax-update/',views.ajax_update_cart,name='ajax_update_cart'),

]
