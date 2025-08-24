from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def notify_event_attendees(event, subject, template_name, context_extra=None):
    """Send HTML email notification to all registered attendees."""
    attendees = event.attendees.all()
    recipient_list = [a.email for a in attendees if a.email]

    if not recipient_list:
        return

    context = {"event": event}
    if context_extra:
        context.update(context_extra)

    # Render both text and HTML
    text_content = render_to_string(f"emails/{template_name}.txt", context)
    html_content = render_to_string(f"emails/{template_name}.html", context)

    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
