from django.urls import path
from . import views


urlpatterns = [
    path('',views.wishlist,name='wishlist'),
    path('add/<int:product_id>/',views.add_to_wishlist,name='add_to_wishlist'),
    path('remove/<int:wishlist_id>/',views.remove_wishlist,name='remove_wishlist'),
    path('wishlist-clear/',views.clear_wishlist,name='clear_wishlist'),
    # path('wishlist-move-all-to-cart/',views.move_all_to_cart,name='move_all_to_cart'),
]
