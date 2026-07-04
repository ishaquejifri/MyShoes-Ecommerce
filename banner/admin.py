from django.contrib import admin
from .models import Banner

# Register your models here.


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title','banner_type','is_active','display_order')
    list_filter = ('banner_type','is_active')
    search_fields = ('title',)
    list_editable = ('is_active','display_order')

    
