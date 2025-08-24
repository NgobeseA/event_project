from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, F
from datetime import datetime
from django.utils import timezone
import json
from django.db.models.functions import TruncDate

from .forms import UserRegistrationForm, AdminUserCreationForm, EventAttendeeRegistrationForm, EventForm
from .models import Event, Attendee, EventRegistration, CustomUser
from .utils import notify_event_attendees

# Create your views here.
def admin_dashboard(request):
    return render(request, 'adminDashboard.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return dashboard(user)
    else:
        form = UserRegistrationForm()

    return render(request, 'registration.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return dashboard(user)
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def dashboard(user):
    if is_admin(user): 
      return redirect('home')
    else:
        return redirect('organizer_overview')

def is_admin(user):
    return user.is_superuser or user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def admin_create_user(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'User {username} created successfully!')
            return redirect('admin_create_user')
    else:
        form = AdminUserCreationForm()
    return render(request, 'create_user.html', {'form': form})

def register_for_event(request, event_id):
    """Register an attendee for an event"""
    event = get_object_or_404(Event,  id=event_id, status=Event.PUBLISHED)

    can_register, message = event.can_register()
    if not can_register:
        messages.error(request, message)
        return redirect('event_details', event_id=event_id)
    
    if request.method == 'POST':
        form = EventAttendeeRegistrationForm(event=event, data=request.POST)
        if form.is_valid():
            try:
                registration = form.save()
                messages.success(request, f'Successfully registered for {event.title}')
                return redirect('event_details')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            messages.error(request, f'Please correct the errors below.')
    else:
        form = EventAttendeeRegistrationForm(event=event)
    
    return render(request, 'event_details.html', {'form': form, 'event': event})


def event_attendees(request, event):
    """
    View attendees for an event organizer only
    """
    registrations = event.regisrations.select_related('attendee').order_by('-registered_at')

    paginator = Paginator(registrations, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj

def attendee_events(request, attendee_id):
    """View events for a specific attendee"""
    attendee = get_object_or_404(Attendee, id=attendee_id)
    registrations = attendee.register.select_related('event').order_by('-registered_at')

    return render(request, '')

@login_required
def organizer_overview(request):
    organizer = request.user
    events = Event.objects.filter(organizer=organizer)


    total_events = events.count()
    published_events_count = events.filter(status=Event.PUBLISHED).count()
    draft_events_count = events.filter(status=Event.DRAFT).count()
    
    # Get current month's start and end dates
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        next_month_start = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month_start = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Upcoming events for this month (from today until end of current month)
    upcoming_events_this_month = events.filter(
        start_date__gte=now.date(),
        start_date__lt=next_month_start.date(),
        status=Event.PUBLISHED
    )
    upcoming_events_count = upcoming_events_this_month.count()
    
    # Total attendees across all events
    total_attendees = events.aggregate(
        total=Count('attendees', distinct=True)
    )['total'] or 0
    
    # Get organizer's events ordered by number of attendees (most attendees first)
    organizer_events = events.annotate(
        attendee_count=Count('attendees')
    ).order_by('-attendee_count', '-created_at')  # Secondary sort by creation date

    category_data = events.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Prepare chart data
    chart_labels = []
    chart_data = []
    chart_colors = []
    
    # Color mapping for each category
    category_colors = {
        Event.MUSIC_ARTS: '#FF6384',
        Event.BUSINESS: '#36A2EB', 
        Event.SPORTS: '#FFCE56',
        Event.TECHNOLOGY: '#4BC0C0',
        Event.FOOD_DRINK: '#9966FF',
        Event.HEALTH_WELLNESS: '#FF9F40',
        Event.EDUCATION: '#FF6384',
        Event.COMMUNITY: '#C9CBCF',
        Event.CHARITY: '#4BC0C0',
        Event.GOVERNMENT: '#36A2EB',
        Event.TOURISM: '#FFCE56'
    }
    
    # Calculate percentages and prepare chart data
    for item in category_data:
        category = item['category']
        count = item['count']
        percentage = round((count / total_events) * 100, 1) if total_events > 0 else 0
        
        # Get category display name
        category_display = dict(Event.CATEGORY_CHOICES).get(category, category)
        
        chart_labels.append(category_display)
        chart_data.append(percentage)
        chart_colors.append(category_colors.get(category, '#C9CBCF'))
    
    # Convert to JSON for JavaScript
    chart_data_json = json.dumps({
        'labels': chart_labels,
        'data': chart_data,
        'colors': chart_colors
    })
    
    print(f"Total events: {total_events}")
    print(f"Published: {published_events_count}, Draft: {draft_events_count}")
    print(f"Upcoming this month: {upcoming_events_count}")
    
    context = {
        'total_events': total_events,
        'published_events_count': published_events_count,
        'draft_events_count': draft_events_count,
        'upcoming_events_count': upcoming_events_count,
        'total_attendees': total_attendees,
        'organizer_events': organizer_events,  # List of events ordered by attendee count
        'category_chart_data': chart_data_json,  # JSON data for Chart.js
        'category_breakdown': category_data,
    }


    return render(request, 'organizer_dashboard.html', context)

@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user  # attach logged-in user
            event.save()
            form.save_m2m()  # save tags/relations
            return redirect("organizer_overview")  # redirect after success
    else:
        form = EventForm()

    return render(request, "create_event.html", {"form": form})

def view_event(request, event_id):
    """
    View function for displaying details of a single event.
    
    Retrieves an event by its primary key (pk) and renders the event detail page.
    
    """
    event = get_object_or_404(Event, id=event_id)
    
    organizer = event.organizer
    organizer_name = event.organizer_name()  # This method already exists in your model
    organizer_contact = organizer.contact_number
    organizer_email = organizer.email

    # user_contact = user.mobile_number
    session_key = f'viewed_event_{event_id}'
    if not request.session.get(session_key):
        Event.objects.filter(id=event_id).update(views_count=F('views_count')+1)
        event.refresh_from_db()
        request.session[session_key] = True
    
    form = EventAttendeeRegistrationForm(event=event)

    context = {
        'event': event,
        'organizer_name': organizer_name,
        'organizer_email': organizer_email,
        'organizer_contact': organizer_contact,
        'form': form,
    }
    return render(request, 'event_details.html', context)

@login_required
def event_analytics(request, event_id):
    user = request.user
    event = get_object_or_404(Event, id=event_id)

    # Ensure only organizer can see analytics
    if user != event.organizer:
        messages.error(request, 'You are not permitted to access this page.')
        return redirect('event_details', event_id=event.id)

    # Example: if you have a field `views` in Event
    total_views = event.views_count 

    # Total registrations (attendees linked via EventRegistration)
    total_registrations = event.attendees.count()

    # Conversion rate (avoid division by zero)
    conversion_rate = 0
    if total_views > 0:
        conversion_rate = round((total_registrations / total_views) * 100, 1)

    # List of registered attendees
    registered_users = event.attendees.all()

    # Group registrations by date
    registrations_over_time = (
        EventRegistration.objects.filter(event=event)
        .annotate(date=TruncDate("registered_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    
    context = {
        'event': event,
        'total_views': total_views,
        'total_registrations': total_registrations,
        'conversion_rate': conversion_rate,
        'registered_users': registered_users,
        'registrations_over_time': list(registrations_over_time),
    }

    return render(request, 'event_analytics.html', context)

@login_required
def cancel_event(request, event_id):
    """Cancel an event and notify all attendees."""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    # Update status
    event.status = Event.CANCELLED
    event.save()

    # Notify attendees
    subject = f"Event Cancelled: {event.title}"
    notify_event_attendees(event, subject, "event_cancelled")

    messages.success(request, f"The event '{event.title}' has been cancelled. Attendees notified.")
    return redirect("event_analytics", event_id=event.id)

def edit_event(request, event_id):
    """Edit an event and notify attendees of updates."""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()

            # Notify attendees
            subject = f"Event Updated: {event.title}"
            notify_event_attendees(event, subject, "event_updated")

            messages.success(request, f"The event '{event.title}' was updated and attendees notified.")
            return redirect("event_details", event_id=event.id)
    else:
        form = EventForm(instance=event)

    return render(request, "events/edit_event.html", {"form": form, "event": event})