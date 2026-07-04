from django import forms
from .models import Coupon,CouponUsage

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = '__all__'

