from django.urls import path
from . import views

urlpatterns = [
    path('banner/', views.banner_list, name='banner_list'),
    path('add/', views.add_banner, name='add_banner'),
    path('edit/<uuid:uuid>/', views.edit_banner, name='edit_banner'),
    path('delete/<uuid:uuid>/', views.delete_banner, name='delete_banner'),
    path('toggle/<uuid:uuid>/', views.toggle_banner, name='toggle_banner'),
]