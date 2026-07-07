from django.contrib import admin
from .models import FAQItem


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ['sort_order', 'question', 'is_active', 'updated_at']
    list_display_links = ['question']
    list_filter = ['is_active']
    search_fields = ['question', 'answer']
    list_editable = ['sort_order']
