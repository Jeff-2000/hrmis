from django.contrib import admin
from .models import Situation

@admin.register(Situation)
class SituationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'situation_type', 'start_date', 'end_date', 'status')
    list_filter = ('situation_type', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'situation_type__name')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)