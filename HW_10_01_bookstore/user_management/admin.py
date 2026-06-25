from django.contrib import admin
import user_management.models as user_management_models

admin.site.register(user_management_models.DeliveryAddress)
admin.site.register(user_management_models.LastViewedBooks)
