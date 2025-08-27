from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Attendee, Event
from django.template.response import TemplateResponse
from django.urls import path

# Register your models here.
class CustomuserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'contact_number', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('contact_number', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('first_name', 'last_name', 'email', 'contact_number', 'role')}),
    )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'start_date', 'end_date', 'start_time', 'end_time', 'venue', 'is_approved')
    list_filter = ('is_approved', 'category', 'status')
    search_fields = ('title', 'organizer')

    actions = ['approve_events']

    def approve_events(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} events(s) successfully approved.')
    approve_events.short_description = "Approve selected events"

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
        pending = Event.objects.filter(is_approve=False)
        context = dict(
            self.each_context(request),
            pending_events=pending,
        )
        return TemplateResponse(request, 'admin/pending_events.html', context)

admin.site.register(CustomUser, CustomuserAdmin)
admin.site.register(Attendee)
custom_admin_site = CustomAdminSite(name='custom_admin')
custom_admin_site.register(Event)