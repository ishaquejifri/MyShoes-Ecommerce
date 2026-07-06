from django import forms
from .models import Banner



class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = "__all__"

        common_class = "w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"

        widgets = {
            "title": forms.TextInput(attrs={"class": common_class}),
            "subtitle": forms.TextInput(attrs={"class": common_class}),
            "button_text": forms.TextInput(attrs={"class": common_class}),
            "button_link": forms.TextInput(attrs={"class": common_class}),
            "banner_type": forms.Select(attrs={"class": common_class}),
            "display_order": forms.NumberInput(attrs={
                "class": common_class,
                "min": 0,
            }),
            "start_date": forms.DateInput(attrs={
                "class": common_class,
                "type": "date",
            }),
            "end_date": forms.DateInput(attrs={
                "class": common_class,
                "type": "date",
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "w-full border rounded-lg px-4 py-2",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "h-5 w-5 text-indigo-600 rounded",
            }),
        }