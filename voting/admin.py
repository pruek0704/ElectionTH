from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import ElectionConfig
from .models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "national_id", "district")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "first_name", "last_name", "national_id", "district", "is_staff", "is_active"),
        }),
    )
    list_display = ("username", "first_name", "last_name", "national_id", "is_staff", "is_active")
    search_fields = ("username", "first_name", "last_name", "national_id")
    ordering = ("username",)

@admin.register(ElectionConfig)
class ElectionConfigAdmin(admin.ModelAdmin):
    list_display = ['is_open', 'opened_at', 'closed_at']