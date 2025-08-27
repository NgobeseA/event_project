from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Attendee

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

admin.site.register(CustomUser, CustomuserAdmin)
admin.site.register(Attendee)