from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib.auth.forms import AuthenticationForm

from .forms import UserRegistrationForm, AdminUserCreationForm, EventAttendeeRegistrationForm, EventForm
from .models import Event, Attendee, EventRegistration

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
    event = get_object_or_404(Event,  id=event, status=Event.PUBLISHED)

    can_register, message = event.can_register()
    if not can_register:
        messages.error(request, message)
        return redirect('event_details', pk=event_id)
    
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
    
    return render(request, 'event_registration.html', {'form': form, 'event': event})

@login_required
def event_attendees(request, event_id):
    """
    View attendees for an event organizer only
    """
    event = get_object_or_404(Event, id=event_id)
    registrations = event.regisrations.select_related('attendee').order_by('-registered_at')

    paginator = Paginator(registrations, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'event_attendees.html', {
        'event': event,
        'registrations': page_obj
    })

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
    print(len(total_events))

    return render(request, 'organizer_dashboard.html')

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

def view_event(request, pk):
    """
    View function for displaying details of a single event.
    
    Retrieves an event by its primary key (pk) and renders the event detail page.
    Also fetches recommended events based on the selected event's category.
    """
    event = get_object_or_404(Event, pk=pk)
    user = event.organizer_name()
    organizer_contact = user.contact_number
    # user_contact = user.mobile_number
    session_key = f'viewed_event_{pk}'
    if not request.session.get(session_key):
        Event.objects.filter(pk=pk).update(views_count=F('views_count')+1)
        event.refresh_from_db()
        request.session[session_key] = True
    
    context = {
        'event': event,
        'organizer_email': user_email,
        'organizer_contact': organizer_contact
    }
    return render(request, 'event_details.html', context)
