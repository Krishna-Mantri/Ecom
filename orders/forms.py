# from django import forms
# from .models import Order

# class OrderCreateForm(forms.ModelForm):
#     class Meta:
#         model=Order
#         fields=["full_name","email","address"]

from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full name',
                'autocomplete': 'name',
                'required': 'required',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your email address',
                'autocomplete': 'email',
                'required': 'required',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your shipping address',
                'rows': 4,
                'required': 'required',
            }),
        }

    # Optional: You can customize field labels
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].label = 'Full Name'
        self.fields['email'].label = 'Email Address'
        self.fields['address'].label = 'Shipping Address'

