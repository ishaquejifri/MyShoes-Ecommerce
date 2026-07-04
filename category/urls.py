from django.urls import path
from . import views

urlpatterns = [
    
    path('',views.category_list,name='category_list'),
    path('add/',views.add_category,name='add_category'),
    path('edit/<int:id>',views.edit_category,name='edit_category'),
    path('toggle/<int:id>',views.toggle_category_status,name='toggle_category_status'),
    path('delete/<int:id>',views.delete_category,name='delete_category'),
    
]
