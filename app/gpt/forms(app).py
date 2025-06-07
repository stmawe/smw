from django import forms
from django.utils.text import slugify
from .models import User, Client, ClientDomain
import json
import os
from django.conf import settings

def get_university_choices():
    file_path = os.path.join(settings.BASE_DIR, 'app', 'university_data.json')
    choices = [('', 'Select your university')]
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            for university in data.get('universities', []):
                choices.append((university['name'], university['name']))
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Could not load or parse university_data.json at {file_path}")
        return [('', 'Could not load universities')]
    return choices

class TenantRegistrationForm(forms.Form):
    """
    Updated form for registering a new tenant and an admin user,
    including username and an optional preferred subdomain.
    """
    first_name = forms.CharField(max_length=100, label="First Name")
    last_name = forms.CharField(max_length=100, label="Last Name")
    username = forms.CharField(max_length=150, label="Username")
    email = forms.EmailField(label="University Email")
    university_name = forms.ChoiceField(
        choices=get_university_choices,
        label="University"
    )
    # This field is now optional
    preferred_subdomain = forms.SlugField(
        max_length=50,
        label="Preferred Subdomain (Optional)",
        required=False,
        help_text="e.g., 'uon-market'. If left blank, one will be generated for you."
    )
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean_username(self):
        """Ensure the username is unique."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        """Ensure the user email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean_university_name(self):
        """Ensure the selected university hasn't already been registered."""
        name = self.cleaned_data.get('university_name')
        if not name:
            raise forms.ValidationError("Please select a university.")
        if Client.objects.filter(name=name).exists():
            raise forms.ValidationError("A tenant for this university already exists.")
        return name

    def clean_preferred_subdomain(self):
        """Ensure the preferred subdomain is unique if provided."""
        subdomain = self.cleaned_data.get('preferred_subdomain')
        if subdomain:
            subdomain = subdomain.lower()
            main_domain = "localhost"  # Change for production
            domain_name = f"{subdomain}.{main_domain}"
            if ClientDomain.objects.filter(domain=domain_name).exists():
                raise forms.ValidationError("This subdomain is already taken. Please try another or leave it blank.")
        return subdomain

    def clean(self):
        """Verify that the two password fields match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password and password2 and password != password2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data
