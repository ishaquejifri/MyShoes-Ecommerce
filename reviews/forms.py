from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ["rating", "review_text"]

        widgets = {
            "rating": forms.NumberInput(
                attrs={
                    "min": 1,
                    "max": 5,
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
                }
            ),
            "review_text": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Share your experience...",
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-green-500 focus:outline-none"
                }
            ),
        }