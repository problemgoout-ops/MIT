from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'first_name', 'last_name', 'telegram',
        'email', 'status', 'source',
    ]
    list_filter = ['status', 'source', 'created_at']
    search_fields = [
        'first_name', 'last_name', 'telegram',
        'email', 'task_description',
    ]
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
    fieldsets = (
        ('Контактные данные', {
            'fields': ('first_name', 'last_name', 'telegram', 'email'),
        }),
        ('Задача', {
            'fields': ('task_description',),
        }),
        ('Статус', {
            'fields': ('status', 'manager_comment'),
        }),
        ('Маркетинг', {
            'fields': (
                'source', 'utm_source', 'utm_medium',
                'utm_campaign', 'utm_content', 'utm_term',
                'page_url',
            ),
        }),
        ('Техническое', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
        }),
    )
