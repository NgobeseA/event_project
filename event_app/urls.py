from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('admin/create-user/', views.admin_create_user, name='admin_create_user'),
    path('events/<int:event_id>/register', views.register_for_event, name='register_for_event'),
    path('organizer-overview/', views.organizer_overview, name='organizer_overview'),
    path('add-event/', views.create_event, name="create_event"),
    path('event-analytics/<int:event_id>/', views.event_analytics, name="event_analytics"),
    path('event-details/<int:event_id>/', views.view_event, name='event_details'),
    path("events/<int:event_id>/cancel/", views.cancel_event, name="cancel_event"),
    path("events/<int:event_id>/edit/", views.edit_event, name="edit_event"),

]