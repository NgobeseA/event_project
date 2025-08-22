from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='home'),
    path('register/', views.register_view, name='register'),
    path('admin/create-user/', views.admin_create_user, name='admin_create_user')
]