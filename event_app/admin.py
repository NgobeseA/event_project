from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
import requests
from django.conf import settings

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import CustomUser, Event


admin.register(CustomUser)
admin.register(Event)