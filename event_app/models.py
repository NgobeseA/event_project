from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
import json

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('organizer', 'Organizer'),
        ('attendee', 'Attendee'),
    ]

    contact_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='organizer')

    def __str__(self):
        return f'{self.username} ({self.role})'

User = get_user_model()

class Event(models.Model):

    MUSIC_ARTS = 'music-arts'
    BUSINESS = 'business'
    SPORTS = 'sports'
    TECHNOLOGY = 'technology'
    FOOD_DRINK = 'food-drink'
    HEALTH_WELLNESS = 'health-wellness'
    EDUCATION = 'education'
    COMMUNITY = 'community'
    CHARITY = 'charity'
    GOVERNMENT = 'government'
    TOURISM = 'tourism'

    CATEGORY_CHOICES = [
        (MUSIC_ARTS, 'Music & Arts'),
        (BUSINESS, 'Business & Professional'),
        (SPORTS, 'Sports & Fitness'),
        (TECHNOLOGY, 'Technology'),
        (FOOD_DRINK, 'Food & Drink'),
        (HEALTH_WELLNESS, 'Health & Wellness'),
        (EDUCATION, 'Education & Learning'),
        (COMMUNITY, 'Community & Culture'),
        (CHARITY, 'Charity & Fundraising'),
        (GOVERNMENT, 'Government & Politics'),
        (TOURISM, 'Tourism & Hospitality'),
    ]

    DRAFT = 'draft'
    PUBLISHED = 'published'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (CANCELLED, 'Cancelled'),
        (PENDING, 'Pending'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=80, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    is_approved = models.BooleanField(default=False)

    attendees = models.ManyToManyField(
        User,
        through='EventRegistrations',
        related_name='events',
        blank=True
    )

    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    venue = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(blank=True, null=True)

    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    tags = models.TextField(help_text='Comma-separated tags', blank=True)

    max_attendees = models.PositiveIntegerField(blank=True, null=True)
    registration_deadline = models.DateTimeField(blank=True, null=True)

    views_count = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    
    def organizer_name(self):
        return f'{self.organizer.first_name} {self.organizer.last_name}'
    
    def get_favorited_by(self):
        return User.objects.filter(event_favorites__event=self)

    @property
    def organizer_email(self):
        return f'{self.organizer.email}'
    
    @property
    def current_attendees(self):
        return self.attendees.count()

    @property
    def tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def is_attendee_registered(self, attendee):
        return self.attendees.filter(id=attendee.id).exists()

    def can_register(self, attendee=None):
        if self.status != self.PUBLISHED:
            return False, 'Event is not published'
        if attendee and self.is_attendee_registered(attendee):
            return False, 'Already registered'
        return True, 'Can register'
    
    def get_category_display_info(self):
        category_info = {
            self.MUSIC_ARTS: {"label": "Music & Arts", "color": "bg-purple-100 text-purple-800"},
            self.BUSINESS: {"label": "Business & Professional", "color": "bg-blue-100 text-blue-800"},
            self.SPORTS: {"label": "Sports & Fitness", "color": "bg-green-100 text-green-800"},
            self.TECHNOLOGY: {"label": "Technology", "color": "bg-gray-100 text-gray-800"},
            self.FOOD_DRINK: {"label": "Food & Drink", "color": "bg-orange-100 text-orange-800"},
            self.HEALTH_WELLNESS: {"label": "Health & Wellness", "color": "bg-emerald-100 text-emerald-800"},
            self.EDUCATION: {"label": "Education & Learning", "color": "bg-yellow-100 text-yellow-800"},
            self.COMMUNITY: {"label": "Community & Culture", "color": "bg-pink-100 text-pink-800"},
            self.CHARITY: {"label": "Charity & Fundraising", "color": "bg-red-100 text-red-800"},
            self.GOVERNMENT: {"label": "Government & Politics", "color": "bg-indigo-100 text-indigo-800"},
            self.TOURISM: {"label": "Tourism & Hospitality", "color": "bg-teal-100 text-teal-800"},
        }
        return category_info.get(self.category, {'label': self.get_category_display(), 'color': 'bg-secondary text-white'})

class EventRegistration(models.Model):
    """
    This is the joining table that stores additional registration
    """
    REGISTRATION_STATUS_CHOICES=[
        ('registered', 'Registered'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    attendee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='regisrations')

    status = models.CharField(max_length=30, choices=REGISTRATION_STATUS_CHOICES, default='registered')
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['event', 'attendee']
        ordering = ['-registered_at']
        verbose_name = 'Event Registration'
        verbose_name_plural = 'Event Registrations'
    
    def __str__(self):
        return f'{self.attendee.full_name} -> {self.event.title}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def can_cancel(self):
        """Check if registration can be cancelled"""
        return self.status == 'registered' and self.event.start_date > timezone.now().date()

    def cancel_registration(self):
        """Cancel this registration"""
        if self.can_cancel:
            self.status = 'cancelled'
            self.updated_at = timezone.now()
            self.save()
            return True
        return False
    
    def __str__(self):
        return f'{self.attendee} favorited "{self.event}" on {self.created_at}'
    
class EventFavorite(models.Model):
    attendee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_favorites')
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='favorites')
    favorited_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('attendee', 'event')
        ordering = ['-favorited_at']
        verbose_name = 'Event Favorite'
        verbose_name_plural = 'Event Favorites'

    def __str__(self):
        return f'{self.attendee} favorited "{self.event}" on {self.favorited_at}'
    

class Budget(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='budget')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def calculate_total(self):
        total = self.items.aggregate(total=models.Sum('amount'))['total'] or 0
        self.total_amount = total
        self.save()
        return total
    
    def __str__(self):
        return f"Budget for {self.event.title} - {self.total_amount}"
    
class BudgetItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return  f"{self.category}: {self.amount}"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.username}: {self.message}'
    
class Rejection(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rejection')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Rejection message for {self.event.title}'

# Dynamic form

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