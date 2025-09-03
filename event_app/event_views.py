from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.db.models.functions import TruncDate
from django.utils.safestring import mark_safe
from django.db.models import Count, F, Avg, Sum
from datetime import datetime
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils.timezone import now
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from .models import Event, Attendee, Notification, Budget, BudgetItem
from .forms import EventAttendeeRegistrationForm, EventForm
from .utils import notify_event_attendees
from django.forms import formset_factory
from .forms import EventBudgetForm, BudgetItemForm, DynamicEventRegistrationForm
from .form_models import FormField, EventRegistrations

User = get_user_model()

def notify_admins(message, url=None):
    channel_layer = get_channel_layer()
    admins = User.objects.filter(is_staff=True)
    print('Tis is running ', len(admins))

    for admin in admins:
        notify = Notification.objects.create(user=admin, message=message, url=url)

        async_to_sync(channel_layer.group_send)(
            f'user_{admin.id}',
            {
                'type': 'send_notification',
                'message': notify.message,
                'url': notify.url,
                'created_at': notify.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

def register_for_event(request, event_id):
    """Register an attendee for an event"""
    event = get_object_or_404(Event,  id=event_id, status=Event.PUBLISHED)

    can_register, message = event.can_register()
    if not can_register:
        messages.error(request, message)
        return redirect('event_details', event_id=event_id)
    
    if request.method == 'POST':
        form = DynamicEventRegistrationForm(event, request.POST, request.FILES)
        if form.is_valid():
            try:
                registration = form.save_registration(user=request.user if request.user.is_authenticated else None)
                messages.success(request, f'Successfully registered for {event.title}')
                return redirect('event_details', event_id=event_id)
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            messages.error(request, f'Please correct the errors below.')
    else:
        form = DynamicEventRegistrationForm(event)
    
    return render(request, 'event_details.html', {'form': form, 'event': event})

@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user  # attach logged-in user
            event.save()
            form.save_m2m()  # save tags/relations

            if event.status == Event.PUBLISHED:
                notify_admins(f'New event "{event.title}" awaiting approval', url=f'/admin/events/{event.id}/preview/')

            return redirect('organizer_overview')
            
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
    
    form = DynamicEventRegistrationForm(event)

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
        EventRegistrations.objects.filter(event=event)
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
    try:
        event = get_object_or_404(Event, id=event_id, organizer=request.user)

        # Update status
        event.status = Event.CANCELLED
        event.save()

        # Notify attendees
        subject = f"Event Cancelled: {event.title}"
        #notify_event_attendees(event, subject, "event_cancelled")

        messages.success(request, f"The event '{event.title}' has been cancelled. Attendees notified.")
    except DatabaseError as db_err:
        messages.error(request, f"Database error: {db_err}")
    except Exception as e:
        messages.error(request, f"Something went wrong: {str(e)}")
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

    return render(request, "create_event.html", {"form": form, "event": event})

def upcoming_events_view(request):
    events = Event.objects.filter(start_date__gte=now(),status=Event.PUBLISHED).order_by('start_date')
    paginator = Paginator(events, 8)  # Show 5 events per page
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)
    return render(request, 'upcoming_events.html', {'events': events})


def event_budget_view(request):
    BudgetItemFormSet = formset_factory(BudgetItemForm, extra=4)

    if request.method == 'POST':
        event_form = EventBudgetForm(request.POST)
        venue_formset = BudgetItemFormSet(request.POST, prefix='venue')
        catering_formset = BudgetItemFormSet(request.POST, prefix='catering')
        decor_formset = BudgetItemFormSet(request.POST, prefix='decor')
        program_formset = BudgetItemFormSet(request.POST, prefix='program')

        if all([event_form.is_valid(), venue_formset.is_valid(), catering_formset.is_valid(), 
                decor_formset.is_valid(), program_formset.is_valid()]):
            # Save or process data here
            return redirect('budget_success')  # Redirect to a success page
    else:
        event_form = EventBudgetForm()
        venue_formset = BudgetItemFormSet(prefix='venue')
        catering_formset = BudgetItemFormSet(prefix='catering')
        decor_formset = BudgetItemFormSet(prefix='decor')
        program_formset = BudgetItemFormSet(prefix='program')

    return render(request, 'budget.html', {
        'event_form': event_form,
        'venue_formset': venue_formset,
        'catering_formset': catering_formset,
        'decor_formset': decor_formset,
        'program_formset': program_formset,
    })

def publish_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        event.status = Event.PENDING
        event.save(update_fields=['status'])

        payload = {
            'event_id': event.id,
            'title': event.title,
            'organizer': event.organizer.username,
            'status': 'PUBLISHED'
        }

    try:
        requests.post(settings.ADMIN_WEBHOOK_URL, json=payload, timeout=5)
    except request.exceptions.RequestException as e:
        messages.error(request, f'webhook failed: {e}. Contact system support.')
        print('Webhook failed:', e)
    
    messages.success(request, f"Event '{event.title}' published and sent for approval!")
    return redirect('event_analytics', event_id=event.id)

#@csrf_exempt
# def event_status_webhook(request):
#     if request.method == 'post':
#         try:
#             data = json.loads(request.body)
#             event_id = data.get('event_id')
#             status = data.get('status')

#             Event.objects.filter(id=event_id).update(is_approved=True if status == 'APPROVED' else False)

#             return JsonResponse({'message': 'Event status updated'}, status=200)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=400)

#     return JsonResponse({'error': 'Invalid method'}, status=405)

def search_events(request):
    query = request.GET.get('query', '')
    print(query)
    events = Event.objects.filter(title=query.strip())
 
    print(f"about to print events: {events}")
    for event in events:
        print(event.title)
    
    return render(request,'upcoming_events.html', {'events': events})

def event_summary_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    budget = Budget.objects.filter(event=event).first()
    budget_items = BudgetItem.objects.filter(budget=budget) if budget else []

    context = {
        'event': event,
        'budget': budget,
        'budget_items': budget_items,
    }
    return render(request, 'summary.html', context)

def form_builder_view(request, event_id):
    '''Allow organizers to edit their event registration form'''
    event = get_object_or_404(Event, id=event_id)
    form_fields = event.form_fields.all().order_by('order')
    context = {
        'event': event,
        'form_fields': form_fields
    }
    return render(request, 'build_form.html', context)

def create_form_field(request, event_id):
    '''AJAX endpoint for organizers to add form fields'''

    if request.method == 'POST' and request.user.is_authenticated:
        event = get_object_or_404(Event, id=event_id, organizer=request.user)

        try:
            field_data = {
                'label': request.POST.get('label'),
                'field_type': request.POST.get('field_type'),
                'placeholder': request.POST.get('placeholder', ''),
                'help_text': request.POST.get('help_text', ''),
                'is_required': request.POST.get('is_required') == 'true',
                'choices': request.POST.get('choices', ''),
                'order': int(request.POST.get('order', 0)),
            }

            form_field = FormField.objects.create(event=event, **field_data)

            return JsonResponse({
                'success': True,
                'field_id': form_field.id,
                'message': 'Field added successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
        
    return JsonResponse({'success': False, 'message': 'Invalid request'})