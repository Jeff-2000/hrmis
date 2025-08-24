from django.contrib import admin
from .models import *

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'document_type',
        'issued_by',
        'issuance_date',
        'status',
        'uploaded_at',
        'content_type',
        'object_id'
    )
    list_filter = ('document_type', 'status', 'issuance_date', 'uploaded_at')
    search_fields = ('issued_by', 'content_text')
    readonly_fields = ('uploaded_at',)
    date_hierarchy = 'issuance_date'