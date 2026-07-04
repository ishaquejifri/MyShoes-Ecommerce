from django import forms
from .models import Product,ProductVariant

class ProductForm(forms.ModelForm):
    
    class Meta:
        model = Product
        fields = [
            'product_name',
            'slug',
            'base_price',
            'description',
            'category',
            'image',
            'offer_price',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False 

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['size','color','stock']
        widgets = {
            'size': forms.TextInput(attrs={
                'class':'w-full rounded-lg bg-[#11221c] border border-[#356454] text-white'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full rounded-lg bg-[#11221c] border border-[#356454] text-white'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg bg-[#11221c] border border-[#356454] text-white'
            }),
        }          






