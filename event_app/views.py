from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, F, Avg, Sum
from datetime import datetime
from django.utils import timezone
import json
from django.utils.timezone import now



from .forms import UserRegistrationForm, AdminUserCreationForm, EventAttendeeRegistrationForm, EventForm
from .models import Event, Attendee, EventRegistration, CustomUser
from .filters import UserFilter

User = get_user_model()
# Create your views here.
def admin_dashboard(request):
    # Stats
    total_users = CustomUser.objects.count()
    total_published_events = Event.objects.filter(status=Event.PUBLISHED).count()
    total_registrations = EventRegistration.objects.count()
    total_views = Event.objects.aggregate(views=Sum("views_count"))["views"] or 0
    avg_conversion_rate = round((total_registrations / total_views * 100), 1) if total_views > 0 else 0

    # Top Organizers (ranked by attendees)
    top_organizers = (
        Event.objects.filter(status=Event.PUBLISHED)
        .annotate(attendee_count=Count("attendees"))
        .values("organizer__id", "organizer__username")
        .annotate(
            total_attendees=Count("attendees"),
            total_events=Count("id")
        )
        .order_by("-total_attendees")[:5]  # Top 5
    )

    # Category usage for pie chart
    category_counts = (
        Event.objects.values("category")
        .annotate(total=Count("id"))
        .order_by("category")
    )
    total_events = Event.objects.count()
    category_data = []
    for c in category_counts:
        percentage = (c["total"] / total_events * 100) if total_events > 0 else 0
        category_data.append({
            "category": c["category"],
            "label": dict(Event.CATEGORY_CHOICES).get(c["category"], "Other"),
            "percentage": round(percentage, 1),
            "color": {
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
            }.get(c["category"], "#999999"),
        })
    
    # Fetching upcomming events
    events = Event.objects.filter(start_date__gte=now(), status=Event.PUBLISHED).order_by('start_date')
    paginator = Paginator(events, 10)
    page_number =  request.GET.get('page')
    upcoming_events = paginator.get_page(page_number)

    context = {
        "total_users": total_users,
        "total_published_events": total_published_events,
        "total_registrations": total_registrations,
        "avg_conversion_rate": avg_conversion_rate,
        "top_organizers": top_organizers,
        "category_data": category_data,
        "upcoming_events": upcoming_events
    }
    return render(request, "adminDashboard.html", context)

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
    if request.method == "POST":
        login_type = request.POST.get("login_type")  # "organizer" or "attendee"

        # ---- ORGANIZER/ADMIN LOGIN ----
        if login_type == "organizer":
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get("username")
                password = form.cleaned_data.get("password")
                user = authenticate(request, username=username, password=password)

                if user is not None:
                    login(request, user)  # Django login for real User/Admin
                    messages.success(request, f"Welcome {user.username}!")
                    return dashboard(user) # adjust to your route
                else:
                    messages.error(request, "Invalid username or password")
            else:
                messages.error(request, "Please correct the errors below.")
        # ---- ATTENDEE LOGIN ----
        elif login_type == "attendee":
            email = request.POST.get("email")
            attendee = Attendee.objects.filter(email=email).first()

            if attendee:
                # Store attendee in session
                request.session["attendee_id"] = attendee.id
                request.session["attendee_name"] = attendee.first_name
                messages.success(request, f"Welcome back, {attendee.first_name}!")
                return redirect("attendee_overview", attendee.id)  # attendee homepage
            else:
                messages.error(request, "Attendee not found. Please register first.")

    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": AuthenticationForm()})

def attendee_login(request):
    print('Attendee Attempt...')
    if request.method == "POST":
        email = request.POST.get('email')  # ✅ use POST instead of clean_data
        user = Attendee.objects.filter(email=email).first()
        print(user)
        if user:
            # You might want to "log in" the attendee in session
            request.session['attendee_id'] = user.id
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('attendee_overview')
        else:
            messages.error(request, "User not found!!")
    return render(request, 'login.html')

def attendee_logout(request):
    """Logs out an attendee by clearing session data"""
    if "attendee_id" in request.session:
        request.session.flush()  # clears all session data
        messages.success(request, "You have been logged out successfully.")
    return redirect("home")

def dashboard(user):
    if is_admin(user): 
      return redirect('admin_dashboard')
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

def logout_view(request):
    logout(request)
    return redirect('home')

def logout_success(request):
    return render(request, 'logout.html')


def home_view(request):
    events = Event.objects.filter(status=Event.PUBLISHED)
    return render(request, 'home.html', {'events': events})


def attendee_overview(request, attendee_id):
    attendee = get_object_or_404(Attendee, id=attendee_id)
    now = timezone.now()

    # Events the user is attending
    events = Event.objects.filter(attendees=attendee).distinct()
    
    total_events = events.count()
    
    upcoming_events = events.filter(start_date__gte=now.date(), status=Event.PUBLISHED)
    upcoming_events_count = upcoming_events.count()
    
    past_events = events.filter(start_date__lt=now.date(), status=Event.PUBLISHED)
    past_events_count = past_events.count()

    # Events grouped by category
    category_data = events.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Prepare chart data
    chart_labels = []
    chart_data = []
    chart_colors = []

    # Color mapping for categories (same as organizer)
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

    for item in category_data:
        category = item['category']
        count = item['count']
        percentage = round((count / total_events) * 100, 1) if total_events > 0 else 0
        category_display = dict(Event.CATEGORY_CHOICES).get(category, category)
        
        chart_labels.append(category_display)
        chart_data.append(percentage)
        chart_colors.append(category_colors.get(category, '#C9CBCF'))

    chart_data_json = json.dumps({
        'labels': chart_labels,
        'data': chart_data,
        'colors': chart_colors
    })

    # Order events by start date (soonest first)
    upcoming_events_ordered = upcoming_events.order_by('start_date')

    print(f"Total registered events: {total_events}")
    print(f"Upcoming events: {upcoming_events_count}, Past events: {past_events_count}")

    context = {
        'attendee': attendee.first_name,
        'total_events': total_events,
        'upcoming_events_count': upcoming_events_count,
        'past_events_count': past_events_count,
        'attendee_events': upcoming_events_ordered,  # or all events, if needed
        'category_chart_data': chart_data_json,
        'category_breakdown': category_data,
    }

    return render(request, 'attendee_dashboard.html', context)

@login_required
def users_list_view(request):
    user = request.user

    if is_admin(user):
        users = User.objects.select_related('attendee_profile').all()
        user_filter = UserFilter(request.GET, queryset=users)
        form = UserRegistrationForm()

        paginator = Paginator(user_filter.qs, 20)
        page_number = request.GET.get('page')

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.number_pages)
        
        context = {
            'total_result': user_filter.qs.count(),
            'filter': user_filter,
            'page_obj': page_obj,
            'form': form,
        }


        return render(request, 'admin/users.html', context)
    else:
        messages.warning(request, 'Only admin can access this page. Please contact the admin')
        return redirect('home')