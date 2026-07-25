from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

INPUT_CLASSES = (
    "w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 "
    "focus:border-teal-500 focus:ring-2 focus:ring-teal-100 "
    "outline-none transition text-sm text-gray-800"
)


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False, max_length=15)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "phone_number", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Enter your name",
            "email": "Enter your email",
            "phone_number": "Enter your phone number (optional)",
            "password1": "Create a password",
            "password2": "Confirm your password",
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({
                "class": INPUT_CLASSES,
                "placeholder": placeholders.get(name, ""),
            })


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": INPUT_CLASSES,
            "placeholder": "Enter your name",
            "autofocus": True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": INPUT_CLASSES,
            "placeholder": "Enter your password",
        })
    )