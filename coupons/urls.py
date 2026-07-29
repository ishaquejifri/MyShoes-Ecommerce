from django.urls import path
from . import views


urlpatterns = [
    path('admin/coupons/',views.coupon_list,name='coupon_list'),
    path('admin/coupons/add/',views.add_coupon,name='add_coupon'),
    path('admin/coupons/edit/<uuid:coupon_uuid>/',views.edit_coupon,name='edit_coupon'),
    path('admin/coupons/delete/<uuid:coupon_uuid>/',views.delete_coupon,name='delete_coupon'),
    path('admin/coupons/toggle/<uuid:coupon_uuid>/',views.toggle_coupon_status,name='toggle_coupon_status'),
    path('admin/coupons/usage/<uuid:coupon_uuid>/',views.coupon_usage_history,name='coupon_usage_history'),

    # User coupon views
    path('available/',views.user_available_coupons,name='user_available_coupons'),
    path('my-usage/',views.user_coupon_usage_history,name='user_coupon_usage_history'),
    path('apply/',views.apply_coupon,name='apply_coupon'),
    path('remove/',views.remove_coupon,name='remove_coupon'),
]
