from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    
    path('',include('home.urls'),name='home'),
    path('user/', include('accounts.urls')),
    path('admin/',include('adminpanel.urls')),
    path('accounts/', include('allauth.urls')),
    path('system-admin/', admin.site.urls),
    path('category/', include('category.urls')),
    path('products/',include('products.urls')),
    path('cart/',include('cart.urls')),
    path('wishlist/',include('wishlist.urls')),
    path('orders/',include('orders.urls')),
    path('coupons/',include('coupons.urls')),
    path('payments/',include('payments.urls')),
    path('offers/',include('offers.urls')),
    path('banner/', include('banner.urls')),

] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
