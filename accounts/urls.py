from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="user_home"),   
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('forget-password/',views.forget_password,name='forget_password'),
    path('new-password/',views.new_password,name='new_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('profile/',views.profile,name='profile'),
    path('profile/edit-profile/',views.edit_profile,name='edit_profile'),
    path('change-password/',views.change_password,name='change_password'),
    path('change-email/',views.change_email,name='change_email'),
    path('email-change-otp/',views.email_change_otp,name='email_change_otp'),
    path('resend-email-otp',views.resend_email_otp,name='resend_email_otp'),
    path('my-address/',views.my_address,name='my_address'),
    path('add-address/',views.add_address,name='add_address'),
    path('edit-address/<int:id>/',views.edit_address,name='edit_address'),
    path('delete-address/<int:id>/',views.delete_address,name='delete_address'),  
    path('wallet/', views.user_wallet, name='user_wallet'),
    path('wallet/verify/', views.verify_wallet_payment, name='verify_wallet_payment'),
]
