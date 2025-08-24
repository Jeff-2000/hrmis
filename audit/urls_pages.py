# audit/urls.py
from django.urls import path, include

from . import views_pages as pages

urlpatterns = [
    path('index/', pages.audit_index_view, name='audit_index_view'),
    path('detail/<int:pk>/', pages.audit_detail_view, name='audit_detail_view'),
    
    
]
