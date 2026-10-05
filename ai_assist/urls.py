from django.urls import path
from . import views

app_name = 'ai_assist'

urlpatterns = [
    path('',views.assist_page,name='assistant'),
    path('search/',views.ai_search,name='ai_search'),
]
