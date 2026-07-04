from django.urls import path
from . import views

urlpatterns = [
    path('banner/', views.banner_list, name='banner_list'),
    path('add/', views.add_banner, name='add_banner'),
    path('edit/<int:id>/', views.edit_banner, name='edit_banner'),
    path('delete/<int:id>/', views.delete_banner, name='delete_banner'),
    path('toggle/<int:id>/', views.toggle_banner, name='toggle_banner'),
]