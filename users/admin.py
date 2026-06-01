from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User, Profile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'groups')
    search_fields = ('username', 'email')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'steam_id')
    search_fields = ('user__username',)
