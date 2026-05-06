from django import forms
from django.utils.text import slugify
from .models import User, ClientDomain


def get_university_choices():
    """
    Return active entities as choices for the university/institution dropdown.
    Reads from the Entity DB model instead of the legacy university_data.json.
    Returns placeholder-only list when no active entities exist.
    """
    from .models import Entity
    choices = [('', 'Select your university')]
    choices += [
        (e.name, e.name)
        for e in Entity.objects.filter(is_active=True).order_by('name')
    ]
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
        """Ensure a university name was selected."""
        name = self.cleaned_data.get('university_name')
        if not name:
            raise forms.ValidationError("Please select a university.")
        return name

    def clean_preferred_subdomain(self):
        """Ensure the preferred subdomain is unique if provided."""
        subdomain = self.cleaned_data.get('preferred_subdomain')
        if subdomain:
            subdomain = subdomain.lower()
            from django.conf import settings
            main_domain = getattr(settings, 'BASE_DOMAIN', 'localhost')
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


# ============================================================
# ENTITY FORMS
# ============================================================

def _validate_subdomain(subdomain, exclude_id=None):
    """
    Validate subdomain: lowercase alphanumeric + hyphens only, unique.
    Returns cleaned subdomain or raises ValidationError.
    """
    import re
    from .models import Entity

    if not subdomain:
        raise forms.ValidationError("Subdomain is required.")

    subdomain = subdomain.lower().strip()

    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$', subdomain):
        raise forms.ValidationError(
            "Subdomain may only contain lowercase letters, digits, and hyphens, "
            "and must start and end with a letter or digit."
        )

    qs = Entity.objects.filter(subdomain=subdomain)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    if qs.exists():
        raise forms.ValidationError(
            f'The subdomain "{subdomain}" is already in use. Please choose another.'
        )

    return subdomain


class EntityRegistrationForm(forms.Form):
    """
    Public self-registration form for institutions.
    Creates an Entity with status=pending awaiting admin approval.
    """
    name = forms.CharField(
        max_length=255,
        label="Institution Name",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. University of Nairobi'}),
    )
    entity_type = forms.CharField(
        max_length=100,
        label="Institution Type",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. University, College, Location, NGO'}),
    )
    subdomain = forms.SlugField(
        max_length=63,
        label="Preferred Subdomain",
        help_text="Lowercase letters, digits, and hyphens only. "
                  "This becomes {subdomain}.smw.pgwiz.cloud",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. uon'}),
    )
    city = forms.CharField(max_length=100, required=False, label="City")
    country = forms.CharField(max_length=100, required=False, label="Country")
    website = forms.URLField(required=False, label="Website")
    contact_email = forms.EmailField(
        label="Contact Email",
        help_text="We'll use this to follow up on your registration.",
    )

    def clean_subdomain(self):
        return _validate_subdomain(self.cleaned_data.get('subdomain'))


class EntityAdminForm(forms.Form):
    """
    Admin create/edit form for Entity records.
    Used by entity_admin_views for both creation and editing.
    """
    name = forms.CharField(max_length=255, label="Institution Name")
    entity_type = forms.CharField(
        max_length=100,
        label="Type",
        help_text='Free-form: "University", "Location", "NGO", etc.',
    )
    subdomain = forms.SlugField(
        max_length=63,
        label="Subdomain",
        help_text="Becomes {subdomain}.smw.pgwiz.cloud",
    )
    admin_user = forms.IntegerField(
        required=False,
        label="Admin User ID",
        help_text="Optional: ID of the user who administers this entity.",
    )
    status = forms.ChoiceField(
        choices=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('suspended', 'Suspended'),
        ],
        label="Status",
        initial='active',
    )
    city = forms.CharField(max_length=100, required=False, label="City")
    country = forms.CharField(max_length=100, required=False, label="Country")
    website = forms.URLField(required=False, label="Website")

    def __init__(self, *args, entity_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_id = entity_id  # used for subdomain uniqueness check on edit

    def clean_subdomain(self):
        return _validate_subdomain(
            self.cleaned_data.get('subdomain'),
            exclude_id=self._entity_id,
        )

    def clean_admin_user(self):
        user_id = self.cleaned_data.get('admin_user')
        if not user_id:
            return None
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise forms.ValidationError(f"No user found with ID {user_id}.")
