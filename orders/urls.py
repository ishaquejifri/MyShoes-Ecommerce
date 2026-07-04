from django.urls import path
from . import views,admin_views


urlpatterns = [
    #user-side
    path('checkout/',views.checkout,name='checkout'),
    path('place-order/',views.place_order,name='place_order'),
    path('success/<str:order_id>/',views.order_success,name='order_success'),
    path('my_orders/',views.my_order,name='my_orders'),
    path('cancel-order/<str:order_id>/',views.cancel_order,name='cancel_order'),
    path('cancel-order-item/<int:item_id>/',views.cancel_order_item,name='cancel_order_item'),
    path('orders/<str:order_id>/',views.order_details,name='order_details'),
    path('return-order/<str:order_id>/',views.return_order,name='return_order'), 
    path('download-invoice/<str:order_id>/',views.download_invoice,name='download_invoice'),

    #admin-side
    path('admin-orders/',admin_views.admin_order_list,name='admin_order_list'),
    path('admin-order-detail/<str:order_id>/',admin_views.admin_order_details,name='admin_order_details'), 
    path('admin-update-order-status/<str:order_id>/',admin_views.admin_update_order_status,name='admin_update_order_status'),
    path('inventory-management/',admin_views.inventory_management,name='inventory_management'),
    path('update-stock/<int:variant_id>/',admin_views.update_stock,name='update_stock'),  
]
