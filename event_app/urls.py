from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views, event_views

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
    path('event-budget/', event_views.event_budget_view, name='event_budget'),
    path('search/', event_views.search_events, name='search'),

    path('users/', views.users_list_view, name='users'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)