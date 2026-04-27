from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Company, CompanyJoinRequest, Project, Task

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'company', 'is_staff')
    list_filter = ('role', 'company', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'company', 'phone', 'position'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'company', 'phone', 'position'),
        }),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Company)
admin.site.register(CompanyJoinRequest)
admin.site.register(Project)
admin.site.register(Task)