
from django.urls import path
from . import views


urlpatterns = [
    path('verify-payment/',views.verify_payment,name='verify_payment'),
    # path('place-order/',views.place_order,name='place_order'),
    path('payment-failed/<int:order_id>/',views.payment_failed,name='payment_failed'),
    path('retry-payment/<int:order_id>/',views.retry_payment,name='retry_payment'),
]
