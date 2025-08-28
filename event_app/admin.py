from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
import requests
from django.conf import settings

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import CustomUser, Attendee, Event

class CustomAdminSite(admin.AdminSite):
    site_header = 'Event Management Admin'
    site_title = 'Event Admin'
    index_title = 'Dashboard'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('pending-events/', self.admin_view(self.pending_events), name='pending-events'),
        ]
        return custom_urls + urls

    def pending_events(self, request):
        pending = Event.objects.filter(is_approved=False)
        context = dict(
            self.each_context(request),
            pending_events=pending,
        )
        return TemplateResponse(request, 'admin/pending_events.html', context)

custom_admin_site = CustomAdminSite(name='custom_admin')

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'contact_number', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('contact_number', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('first_name', 'last_name', 'email', 'contact_number', 'role')}),
    )

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'start_date', 'end_date', 'start_time', 'end_time', 'venue', 'is_approved', 'preview_action')
    list_filter = ('is_approved', 'category', 'status')
    search_fields = ('title', 'organizer__username')
    actions = ['approve_events']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/preview/', self.admin_site.admin_view(self.preview_event), name='event_app_event_preview'),
        ]
        return custom_urls + urls

    def preview_action(self, obj):
        from django.utils.html import format_html
        return format_html('<a class="button" href="{}">Preview</a>',
                           f"{obj.pk}/preview/")
    preview_action.short_description = 'Preview'

    @admin.action(description='Approve selected events')
    def approve_events(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} events(s) successfully approved.')

    def preview_event(self, request, object_id, *args, **kwargs):
        event = get_object_or_404(Event, id=object_id)
        if request.method == 'POST':
            action = request.POST.get('action')
            status = ''
            if action == 'approve':
                event.is_approved = True
                status = 'APPROVED'
            elif action == 'reject':
                event.is_approved = False
                status = 'REJECTED'
            event.save()

            payload = {
                'event_id': event.id,
                'title': event.title,
                'status': status,
            }
            try:
                requests.post(settings.ORGANIZER_WEBHOOK_URL, json=payload, timeout=5)
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(f'organizer_{event.organizer.id}',{
                    'type': 'event_status_update',
                    'event': {
                        'event_id': event.id,
                        'title': event.title,
                        'status': status,
                    }
                })
            except Exception as e:
                print("Webhook back to organizer failed:", e)

            self.message_user(request, f"Event '{event.title}' {status.lower()} successfully.")
            return redirect('..')
        
        context = dict(
            self.admin_site.each_context(request),
            event=event,
            opts=self.opts,
        )
        return render(request, 'admin/preview.html', context)

custom_admin_site.register(CustomUser, CustomUserAdmin)
custom_admin_site.register(Attendee)
custom_admin_site.register(Event, EventAdmin)