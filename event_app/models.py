from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils import timezone


# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('organizer', 'Organizer'),
    ]

    contact_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='organizer')

    def __str__(self):
        return f'{self.username} ({self.role})'

User = get_user_model()

class Attendee(models.Model):
    """
    Model to store attendee information
    An attendee can register for multiple events
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True, related_name='attendee_profile')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        verbose_name = 'Attendee'
        verbose_name_plural = 'Attendees'
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_registered_events(self):
        """Get all events this attendee is registered for"""
        return self.events.filter(status=Event.PUBLISHED)

    def get_upcoming_events(self):
        return self.events.filter(status = Event.PUBLISHED, start_date_gte=timezone.now().date())

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
    COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=80, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')

    attendees = models.ManyToManyField(
        Attendee,
        through='EventRegistration',
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

    views_count = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def organizer_name(self):
        return f'{self.organizer.first_name} {self.organizer.last_name}'

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
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name='regisrations')

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