from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Attendee, Event, EventRegistration

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Number'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'contact_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.contact_number = self.cleaned_data['contact_number']
        user.role = 'organizer'
        if commit:
            user.save()
        return user

class AdminUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'contact_number', 'role', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.contact_number = self.cleaned_data['contact_number']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user

class AttendeeRegistrationForm(forms.ModelForm):
    """Form for attendee registration"""
    class Meta:
        model = Attendee
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not self.instance.pk and Attendee.objects.filter(email=email).exists():
            pass
        return email
    
class EventAttendeeRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )

    def __init__(self, event=None, *args, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        if email and self.event:
            attendee = Attendee.objects.filter(email=email).first()
            if attendee and self.event.is_attendee_registered(attendee):
                raise forms.validationError('This email is already registered for this event.')
            
            can_register, message = self.event.can_register()

            if not can_register:
                raise forms.validationError(message)
        return cleaned_data
    
    def save(self):
        """Create or get attendee and register for event"""
        email = self.cleaned_data['email']

        attendee, created = Attendee.objects.get_or_create(
            email = email,
            defaults = {
                'first_name': self.cleaned_data['first_name'],
                'last_name': self.cleaned_data['last_name'],
            }
        )

        # If attendee exists, update their information
        if not created:
            attendee.first_name = self.cleaned_data['first_name']
            attendee.last_name = self.cleaned_data['last_name']
            attendee.save()

        # Create registration
        registration = EventRegistration.objects.create(
            event=self.event,
            attendee=attendee,
        )

        return registration

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title", "description", "category", "status",
            "start_date", "end_date", "start_time", "end_time",
            "venue", "city", "is_online", "online_link", "image", "tags",
            "max_attendee", "registration_deadline",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "venue": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "online_link": forms.URLInput(attrs={"class": "form-control"}),
            "tags": forms.TextInput(attrs={"placeholder": "music, conference, free", "class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "is_online": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "max_attendee": forms.NumberInput(attrs={"type": "date", "class": "form-control"}),
            "registration_deadline": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

        }
class BudgetItemForm(forms.Form):
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Item'}))
    budget = forms.DecimalField(required=False, decimal_places=2, max_digits=10)
    

class EventBudgetForm(forms.Form):
    event_name = forms.CharField(max_length=255)
    date = forms.CharField(max_length=100)
    total_budget = forms.DecimalField(decimal_places=2, max_digits=10)