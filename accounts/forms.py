from django import forms
from .models import CustomUser,Address
from django.contrib.auth import authenticate
import re

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'full_name',
            'phone',
            'address_line',
            'street',
            'city',
            'state',
            'postal_code',
            'is_default'
        ] 


    def clean_full_name(self):
        full_name = self.cleaned_data['full_name'].strip()

        if len(full_name) < 3:
            raise forms.ValidationError(
            "Full name must be at least 3 characters long."
        )

        if not re.fullmatch(r'^[A-Za-z ]+$', full_name):
            raise forms.ValidationError(
            "Full name should contain only letters and spaces."
        )

        return full_name
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']

        if not re.fullmatch(r'^\d{10}$', phone):
            raise forms.ValidationError(
            "Phone number must contain exactly 10 digits."
        )

        if len(set(phone)) == 1:
            raise forms.ValidationError(
            "Invalid phone number."
        )

        return phone
    
    def clean_street(self):
        street = self.cleaned_data['street'].strip()

        if len(street) < 3:
            raise forms.ValidationError(
            "Street name is too short."
        )

        return street


    def clean_city(self):
        city = self.cleaned_data['city']

        if not re.fullmatch(r'^[A-Za-z ]+$', city):
            raise forms.ValidationError(
            "City should contain only letters."
            )

        return city

    def clean_state(self):
        state = self.cleaned_data['state']

        if not re.fullmatch(r'^[A-Za-z ]+$', state):
            raise forms.ValidationError(
            "State should contain only letters."
        )

        return state        
    
    def clean_postal_code(self):
        postal_code = self.cleaned_data['postal_code']

        if not re.fullmatch(r'^\d{6}$', postal_code):
            raise forms.ValidationError(
            "Pincode must contain exactly 6 digits."
        )

        return postal_code
    
    def clean_address_line(self):
        address = self.cleaned_data['address_line']

        if len(address.strip()) < 5:
            raise forms.ValidationError(
            "Enter a complete address."
        )

        return address