from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('admin/create-user/', views.admin_create_user, name='admin_create_user'),
    path('events/<int:pk>/register', views.register_for_event, name='register_for_event'),
    path('organizer-overview/', views.organizer_overview, name='organizer_overview'),
    path('add-event/', views.create_event, name="create_event"),
]