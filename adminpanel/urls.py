from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('userlist/', views.user_list, name='user_list'),
    path('sales-report/', views.admin_sales_report, name='admin_sales_report'),
    path('sales-report/download/pdf/', views.download_sales_report_pdf, name='download_sales_report_pdf'),
    path('sales-report/download/excel/', views.download_sales_report_excel, name='download_sales_report_excel'),
    path('toggle-block/<int:user_id>', views.toggle_block_user, name='toggle_block_user'),
]

