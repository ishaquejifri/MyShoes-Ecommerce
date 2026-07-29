from django.urls import path
from . import views


urlpatterns = [
    path('',views.wishlist,name='wishlist'),
    path('add/<uuid:product_uuid>/',views.add_to_wishlist,name='add_to_wishlist'),
    path('remove/<uuid:wishlist_uuid>/',views.remove_wishlist,name='remove_wishlist'),
    path('wishlist-clear/',views.clear_wishlist,name='clear_wishlist'),
    # path('wishlist-move-all-to-cart/',views.move_all_to_cart,name='move_all_to_cart'),
]
