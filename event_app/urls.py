from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views, event_views, admin_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/create-user/', views.admin_create_user, name='admin_create_user'),
    path('events/<int:event_id>/register', event_views.register_for_event, name='register_for_event'),
    path('organizer-overview/', views.organizer_overview, name='organizer_overview'),
    path('add-event/', event_views.create_event, name="create_event"),
    path('event-analytics/<int:event_id>/', event_views.event_analytics, name="event_analytics"),
    path('event-details/<int:event_id>/', event_views.view_event, name='event_details'),
    path("events/<int:event_id>/cancel/", event_views.cancel_event, name="cancel_event"),
    path("events/<int:event_id>/edit/", event_views.edit_event, name="edit_event"),
    path('login/', views.attendee_login, name='attendee_login'),
    path('logout/', views.logout_view, name='logout'),
    path("attendee/logout/", views.attendee_logout, name="attendee_logout"),
    path('upcoming/', event_views.upcoming_events_view, name='upcoming_events'),
    path('attendee_overview/<int:attendee_id>/', views.attendee_overview, name='attendee_overview'),
    path('event-budget/<int:event_id>/', event_views.event_budget_view, name='event_budget'),
    path('search/', event_views.search_events, name='search'),
    path('events/<int:event_id>/summary/', event_views.event_summary_view, name='event_summary'),
    path('events/<int:event_id>/form-builder/', event_views.form_builder_view, name='form_builder'),
    path('events/<int:event_id>/publish/', event_views.publish_event, name="publish_event"),

    # AJAX endpoint
    path('api/event/<int:event_id>/add-field/', event_views.create_form_field, name='create_form_field'),

    #admin endpoint
    path('users/', views.users_list_view, name='users'),
    path('events/', admin_views.events_list_view, name='events'),
    path('events/<int:event_id>/preview', admin_views.preview_event, name='preview'),
    path('events/<int:event_id>/approve/', admin_views.event_approval_view, name='approval'),
    #path('events/<int:event_id>/edit', admin_views.admin_edit_event, name='admin_edit_event'),
    path('users/<int:user_id>/profile/', views.get_user_profile_view, name='user_profile'),
    path('events/<int:event_id>/reject/', admin_views.reject_event_view, name='reject_event')
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)