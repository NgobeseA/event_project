from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Event, Rejection
from .forms import EventForm
from .form_models import EventRegistrations

@login_required
def events_list_view(request):
    events = Event.objects.exclude(status=Event.DRAFT).order_by('-created_at')

    return render(request, 'admin/events.html', {'events': events})

def preview_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    return render(request, 'admin/preview.html', {'event': event})

def admin_delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        pass

def event_approval_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        event.status = Event.PUBLISHED
        event.save()
        event.save(update_fields=['status']) 

        messages.success(request, f'{event.title} has been successfully approved!!')
        return redirect('preview', event_id)
    
    messages.warning(request, 'event only approved by via POST')
    return render(request, 'admin/preview.html', {'event': event})
    

@login_required
def reject_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        admin = request.user
        message = request.POST.get('message', '')

        Rejection.objects.create(event=event, admin=admin, message=message)

        event.status = Event.REJECTED
        event.save()
        return redirect('preview', event_id)
    
    return render(request, 'admin/preview.html', {'event': event})

@login_required
def registered_user_in_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    attendees = EventRegistrations.objects.filter(event=event)

    context = {
        'event': event,
        'attendees': attendees
    }
    return render(request, 'admin/event_registered_user.html', context)
