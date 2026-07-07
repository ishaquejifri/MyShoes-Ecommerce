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
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False 

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['size','color','stock']
        widgets = {
            'size': forms.Select(attrs={
                'class':'w-full rounded-lg bg-[#11221c] border border-[#356454] text-white'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full rounded-lg bg-[#11221c] border border-[#356454] text-white'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg bg-[#11221c] border border-[#356454] text-white'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        size = cleaned_data.get('size')
        color = cleaned_data.get('color')

        if size and color:
            product = self.instance.product if self.instance.pk else self.initial.get('product')

            variant = ProductVariant.objects.filter(
                product = product,
                size__iexact=size.strip(),
                color__iexact=color.strip()
            )                 

            if self.instance.pk:
                variant = variant.exclude(pk=self.instance.pk)

            if variant.exists():
                raise forms.ValidationError(
                    'This size and color combination is already exists for this product.'
                )
        
        return cleaned_data





