from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Company, CompanyJoinRequest, Project, Task

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'company', 'is_staff', 'is_active_member')
    list_filter = ('role', 'company', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'company', 'phone', 'position', 'joined_at'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'company', 'phone', 'position'),
        }),
    )
    readonly_fields = ('joined_at',)
    
    def is_active_member(self, obj):
        return obj.is_active_member()
    is_active_member.boolean = True
    is_active_member.short_description = 'Активный сотрудник'

admin.site.register(User, CustomUserAdmin)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'get_owner')
    search_fields = ('name',)
    
    def get_owner(self, obj):
        owner = obj.get_owner()
        return owner.username if owner else 'Нет владельца'
    get_owner.short_description = 'Владелец'

@admin.register(CompanyJoinRequest)
class CompanyJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'status', 'created_at')
    list_filter = ('status', 'company')
    search_fields = ('user__username', 'company__name')
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        for req in queryset:
            req.approve()
        self.message_user(request, f'Одобрено {queryset.count()} заявок')
    approve_requests.short_description = 'Одобрить выбранные заявки'
    
    def reject_requests(self, request, queryset):
        for req in queryset:
            req.reject()
        self.message_user(request, f'Отклонено {queryset.count()} заявок')
    reject_requests.short_description = 'Отклонить выбранные заявки'

admin.site.register(Project)
admin.site.register(Task)