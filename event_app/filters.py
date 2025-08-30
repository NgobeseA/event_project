import django_filters
from django.contrib.auth import get_user_model
from django import forms
from datetime import date

User = get_user_model()

class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by email...'
        }),
        label='Email'
    )
    registered_month = django_filters.DateFilter(
        field_name = 'created_at',
        lookup_expr = 'month',
        widget = forms.Select(choices=[
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), 
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), 
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ])
    )

    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('organizer', 'Organizer'),
        ('attendee', 'Attendee'),
    ]
    
    role_choice = django_filters.ChoiceFilter(
        field_name='role',
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='All Roles'
    )

    def filter_by_role(self, queryset, name, value):
        if value == 'attendee':
            return queryset.filter(attendee_isnull=False)
    
    class Meta:
        model = User
        fields = ['email','registered_month', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.form.fields.items():
            field.widget.attrs.update({'class': 'form-control'})