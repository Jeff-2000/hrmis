# feedback/admin.py
from django.contrib import admin
from .feedback_models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id","user","rating","status","page_url","created_at")
    list_filter  = ("rating","status","created_at")
    search_fields = ("comment","user__username","page_url")
