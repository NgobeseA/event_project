from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

from .models import Event, Budget, BudgetItem, FormField, EventRegistrations, RegistrationFieldValue

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control border rounded p-2 bg-light', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'foorm-control border rounded p-2 bg-light', 'placeholder': 'Email'})
    )
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control border rounded p-2 bg-light', 'placeholder': 'Contact Number'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'border rounded p-2 bg-light w-100 form-control', 'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control border rounded p-2 bg-light', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control border rounded p-2 bg-light', 'placeholder': 'Confirm Password'})
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
        widget=forms.TextInput(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'border rounded p-2 bg-light w-100 form-control', 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control border rounded p-2 bg-light'})
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

class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'contact_number', 'role',)

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'border rounded p-2 bg-light w-100 form-control', 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control border rounded p-2 bg-light'})
    )


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title", "description", "category", "status",
            "start_date", "end_date", "start_time", "end_time",
            "venue", "city", "is_online", "online_link", "image", "tags",
            "max_attendees", "registration_deadline",
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
            "max_attendees": forms.NumberInput(attrs={"type": "date", "class": "form-control"}),
            "registration_deadline": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

        }

class BudgetItemForm(forms.Form):
    class Meta:
        model = BudgetItem
        fields = ['name', 'amount']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Item'}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Amount'}),
        }
    
class EventBudgetForm(forms.Form):
    event_name = forms.CharField(max_length=255)
    date = forms.CharField(max_length=100)
    total_budget = forms.DecimalField(decimal_places=2, max_digits=10)

class DynamicEventRegistrationForm(forms.Form):
    '''Dynamically generated form based on event's form fields '''

    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

        # Built in fields
        self.fields['email'] = forms.EmailField(label='Email Address', required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
        self.fields['first_name'] = forms.CharField(label='First Name', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
        self.fields['last_name'] = forms.CharField(label='Last Name', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
        self.fields['username'] = forms.CharField(label='Username', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

        # dynamic fields
        for form_field in event.form_fields.all().order_by('order'):
            field_name = f'field_{form_field.id}'
            django_field = self.create_django_field(form_field)
            self.fields[field_name] = django_field

    def create_django_field(self, form_field):
        '''Create appropriate Django form field based on FormField type'''
        common_attrs = {'class': 'form-control'}

        if form_field.placeholder:
            common_attrs['placeholder'] = form_field.placeholder

        field_kwargs = {'label': form_field.label, 'required': form_field.is_required, 'help_text': form_field.help_text,}
        
        if form_field.field_type == 'text':
            field_kwargs['widget'] = forms.TextInput(attrs=common_attrs)
            if form_field.max_length:
                field_kwargs['max_length'] = form_field.max_length
            return forms.CharField(**field_kwargs)
            
        elif form_field.field_type == 'textarea':
            field_kwargs['widget'] = forms.Textarea(attrs={**common_attrs, 'rows': 4})
            return forms.CharField(**field_kwargs)
            
        elif form_field.field_type == 'email':
            field_kwargs['widget'] = forms.EmailInput(attrs=common_attrs)
            return forms.EmailField(**field_kwargs)
            
        elif form_field.field_type == 'phone':
            field_kwargs['widget'] = forms.TextInput(attrs=common_attrs)
            return forms.CharField(**field_kwargs)
            
        elif form_field.field_type == 'number':
            field_kwargs['widget'] = forms.NumberInput(attrs=common_attrs)
            if form_field.min_value is not None:
                field_kwargs['min_value'] = form_field.min_value
            if form_field.max_value is not None:
                field_kwargs['max_value'] = form_field.max_value
            return forms.FloatField(**field_kwargs)
            
        elif form_field.field_type == 'date':
            field_kwargs['widget'] = forms.DateInput(attrs={**common_attrs, 'type': 'date'})
            return forms.DateField(**field_kwargs)
            
        elif form_field.field_type == 'datetime':
            field_kwargs['widget'] = forms.DateTimeInput(attrs={**common_attrs, 'type': 'datetime-local'})
            return forms.DateTimeField(**field_kwargs)
            
        elif form_field.field_type == 'select':
            choices = [(choice, choice) for choice in form_field.get_choices_list()]
            field_kwargs['choices'] = [('', '-- Select --')] + choices
            field_kwargs['widget'] = forms.Select(attrs=common_attrs)
            return forms.ChoiceField(**field_kwargs)
            
        elif form_field.field_type == 'radio':
            choices = [(choice, choice) for choice in form_field.get_choices_list()]
            field_kwargs['choices'] = choices
            field_kwargs['widget'] = forms.RadioSelect()
            return forms.ChoiceField(**field_kwargs)
            
        elif form_field.field_type == 'checkbox':
            choices = [(choice, choice) for choice in form_field.get_choices_list()]
            field_kwargs['choices'] = choices
            field_kwargs['widget'] = forms.CheckboxSelectMultiple()
            field_kwargs['required'] = False  # MultipleChoiceField handles required differently
            return forms.MultipleChoiceField(**field_kwargs)
            
        elif form_field.field_type == 'boolean':
            field_kwargs['widget'] = forms.CheckboxInput()
            return forms.BooleanField(**field_kwargs)
            
        elif form_field.field_type == 'file':
            field_kwargs['widget'] = forms.FileInput(attrs=common_attrs)
            return forms.FileField(**field_kwargs)
        
        # Default fallback
        return forms.CharField(**field_kwargs)
    
    def save_registration(self, user=None):
        """Save the registration and field values"""
        # Create registration
        registration = EventRegistrations.objects.create(
            event=self.event,
            user=user,
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        
        # Save dynamic field values
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('field_'):
                field_id = int(field_name.replace('field_', ''))
                try:
                    form_field = FormField.objects.get(id=field_id, event=self.event)
                    field_value = RegistrationFieldValue.objects.create(
                        registration=registration,
                        form_field=form_field
                    )
                    field_value.set_value(value)
                    field_value.save()
                except FormField.DoesNotExist:
                    continue
        
        return registration