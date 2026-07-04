from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin

# Register your models here.

class AccountAdmin(UserAdmin):
    list_display = ("username","email", "first_name", "last_name","is_staff")
    search_fields = ("email", "first_name")
    readonly_fields = ("date_joined",)
    ordering = ("email",)

admin.site.register(CustomUser,AccountAdmin)