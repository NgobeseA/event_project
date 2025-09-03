from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import json

from .models import Event

User = get_user_model()

class FormField(models.Model):
    ''' Dynamic form field for event registration'''
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('email', 'Email'),
        ('phone', 'Phone Number'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('datetime', 'Date and Time'),
        ('select', 'Dropdown Select'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkboxes'),
        ('boolean', 'Yes/No Checkbox'),
        ('file', 'File Upload'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='form_fields')
    label = models.CharField(max_length=200, help_text='Field label shown to users')
    field_type = models.CharField(max_length=30, choices=FIELD_TYPES)
    placeholder = models.CharField(max_length=200, blank=True, help_text="Placeholder text for input fields")
    help_text = models.CharField(max_length=500, blank=True, help_text="Additional help text for users")
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, help_text="Field display order")
    
    # For select, radio, checkbox fields - store as JSON
    choices = models.TextField(
        blank=True, 
        help_text="JSON array of choices for select/radio/checkbox fields. Example: [\"Option 1\", \"Option 2\"]"
    )
    
    # Field validation
    min_length = models.PositiveIntegerField(null=True, blank=True)
    max_length = models.PositiveIntegerField(null=True, blank=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event.title} - {self.label}"

    def clean(self):
        """Validate field configuration"""
        if self.field_type in ['select', 'radio', 'checkbox'] and not self.choices:
            raise ValidationError("Choices are required for select, radio, and checkbox fields")
        
        if self.choices:
            try:
                choices_list = json.loads(self.choices)
                if not isinstance(choices_list, list):
                    raise ValidationError("Choices must be a JSON array")
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for choices")

    def get_choices_list(self):
        """Return choices as Python list"""
        if self.choices:
            try:
                return json.loads(self.choices)
            except json.JSONDecodeError:
                return []
        return []

    class Meta:
        ordering = ['order', 'id']

class EventRegistrations(models.Model):
    '''User registration for event'''
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow anonymous registrations
    email = models.EmailField()  # Always capture email for contact
    registered_at = models.DateTimeField(auto_now_add=True)

    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        if self.user:
            return f"{self.user.get_full_name()} - {self.event.title}"
        return f"{self.first_name} {self.last_name} - {self.event.title}"

    class Meta:
        unique_together = ['event', 'email']  # Prevent duplicate registrations
        ordering = ['-registered_at']
    
class RegistrationFieldValue(models.Model):
    """Store dynamic field values for each registration"""
    registration = models.ForeignKey(EventRegistrations, on_delete=models.CASCADE, related_name='field_values')
    form_field = models.ForeignKey(FormField, on_delete=models.CASCADE)
    
    # Store different value types
    text_value = models.TextField(blank=True, null=True)
    number_value = models.FloatField(blank=True, null=True)
    date_value = models.DateField(blank=True, null=True)
    datetime_value = models.DateTimeField(blank=True, null=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    file_value = models.FileField(upload_to='registration_files/', blank=True, null=True)
    
    # For multiple choice fields (checkboxes)
    selected_choices = models.TextField(blank=True, help_text="JSON array of selected choices")

    def __str__(self):
        return f"{self.registration} - {self.form_field.label}"

    def get_value(self):
        """Return the appropriate value based on field type"""
        field_type = self.form_field.field_type
        
        if field_type in ['text', 'textarea', 'email', 'phone', 'select', 'radio']:
            return self.text_value
        elif field_type == 'number':
            return self.number_value
        elif field_type == 'date':
            return self.date_value
        elif field_type == 'datetime':
            return self.datetime_value
        elif field_type == 'boolean':
            return self.boolean_value
        elif field_type == 'file':
            return self.file_value
        elif field_type == 'checkbox':
            if self.selected_choices:
                try:
                    return json.loads(self.selected_choices)
                except json.JSONDecodeError:
                    return []
            return []
        return None

    def set_value(self, value):
        """Set the appropriate value based on field type"""
        field_type = self.form_field.field_type
        
        # Clear all values first
        self.text_value = None
        self.number_value = None
        self.date_value = None
        self.datetime_value = None
        self.boolean_value = None
        self.file_value = None
        self.selected_choices = ""
        
        if field_type in ['text', 'textarea', 'email', 'phone', 'select', 'radio']:
            self.text_value = str(value) if value else None
        elif field_type == 'number':
            self.number_value = float(value) if value else None
        elif field_type == 'date':
            self.date_value = value
        elif field_type == 'datetime':
            self.datetime_value = value
        elif field_type == 'boolean':
            self.boolean_value = bool(value)
        elif field_type == 'file':
            self.file_value = value
        elif field_type == 'checkbox':
            if isinstance(value, list):
                self.selected_choices = json.dumps(value)
            else:
                self.selected_choices = json.dumps([value] if value else [])

    class Meta:
        unique_together = ['registration', 'form_field']