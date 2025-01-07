from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Agency, VerificationToken

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
        ('Banking Information',{'fields':('bank_name', 'account_number', 'bank_branch_code', 'account_type', 'account_name')})
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

@admin.register(VerificationToken)
class VerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user', 'created_at', 'expires_at', 'used', 'get_user_email')
    list_filter = ('used', 'created_at', 'expires_at')
    search_fields = ('token', 'user__email', 'user__username')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    
    # Add helpful actions for token management
    actions = ['mark_as_used', 'mark_as_unused', 'extend_expiration']

    def mark_as_used(self, request, queryset):
        updated = queryset.update(used=True)
        self.message_user(request, f'{updated} tokens marked as used.')
    mark_as_used.short_description = "Mark selected tokens as used"

    def mark_as_unused(self, request, queryset):
        updated = queryset.update(used=False)
        self.message_user(request, f'{updated} tokens marked as unused.')
    mark_as_unused.short_description = "Mark selected tokens as unused"

    def extend_expiration(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        # Extend by 24 hours from now
        updated = queryset.update(expires_at=timezone.now() + timedelta(hours=24))
        self.message_user(request, f'Extended expiration for {updated} tokens.')
    extend_expiration.short_description = "Extend expiration by 24 hours"

    # Customize the admin display
    fieldsets = (
        ('Token Information', {
            'fields': ('id', 'token', 'user')
        }),
        ('Status', {
            'fields': ('used', 'created_at', 'expires_at')
        }),
    )

admin.site.register(Agency, AgencyAdmin)