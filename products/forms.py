import re
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

    def clean_product_name(self):
        product_name = self.cleaned_data.get('product_name','').strip()
        if not product_name:
            raise forms.ValidationError('Product name is required.')
        if re.search(r'[^a-zA-Z0-9\s]', product_name):
            raise forms.ValidationError('Product name should not contain special characters.')
        if not re.search(r'[a-zA-Z]', product_name):
            raise forms.ValidationError('Product name should contain at least one letter.')
        if len(product_name) < 3:
            raise forms.ValidationError('Product name should be at least 3 characters long.')
        return product_name

    def clean_slug(self):
        slug = self.cleaned_data.get('slug','').strip().lower()
        if not slug:
            raise forms.ValidationError('Slug is required.')
        if re.match(r'[^a-z0-9-]', slug):
            raise forms.ValidationError('Slug should only contain lowercase letters, numbers, and hyphens.')
        return slug

    def clean_base_price(self):
        base_price = self.cleaned_data.get('base_price')
        if base_price is None:
            raise forms.ValidationError('Base price is required.')
        if base_price <= 0:
            raise forms.ValidationError('Base price must be a positive number.')
        if base_price < 1999:
            raise forms.ValidationError('Base price must be at least ₹ 1999.')
        return base_price

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





