from django.urls import path
from . import views

urlpatterns = [
    
    path('',views.category_list,name='category_list'),
    path('add/',views.add_category,name='add_category'),
    path('edit/<uuid:uuid>/',views.edit_category,name='edit_category'),
    path('toggle/<uuid:uuid>/',views.toggle_category_status,name='toggle_category_status'),
    path('delete/<uuid:uuid>/',views.delete_category,name='delete_category'),
    
]
