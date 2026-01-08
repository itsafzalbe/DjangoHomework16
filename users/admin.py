from django.contrib import admin
from .models import User, UserConfirmation

class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'phone_number']

admin.site.register(User, UserAdmin)


class UserConfirmationAdmin(admin.ModelAdmin):
    list_display = ['verify_type', 'code', 'confirmed']

admin.site.register(UserConfirmation, UserConfirmationAdmin)