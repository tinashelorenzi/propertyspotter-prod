from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Agency

# Custom User Admin to manage CustomUser model with custom fields
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'agency', 'phone', 'created_at', 'last_login')
    list_filter = ('role', 'agency', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'role', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_login')  # Add this line to make these fields read-only
   
    # The following fields are used to manage the user creation form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_image', 'profile_image_url')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),  # These will be read-only
        ('Agency', {'fields': ('agency',)}),
    )
   
    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'groups', 'user_permissions')}),
        ('Agency', {'fields': ('agency',)}),
    )
    filter_horizontal = ('groups', 'user_permissions')

# Register the CustomUser model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)

# Register the Agency model
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at', 'master_user')
    search_fields = ('name', 'email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)  # Add this line for Agency model too

    fieldsets = (
        (None, {'fields': ('name', 'email', 'phone')}),
        ('Additional Info', {'fields': ('address', 'is_active', 'license_valid_until')}),
        ('Master User', {'fields': ('master_user',)}),
        ('Important dates', {'fields': ('created_at',)}),
    )

admin.site.register(Agency, AgencyAdmin)