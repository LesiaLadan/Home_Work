from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, DeliveryAddress, LastViewedBooks

admin.site.register(DeliveryAddress)
admin.site.register(LastViewedBooks)
admin.site.register(User, UserAdmin)
