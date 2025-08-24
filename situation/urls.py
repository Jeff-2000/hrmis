from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SituationViewSet
from django.shortcuts import render
from . import views
router = DefaultRouter()
router.register(r'situations', SituationViewSet, basename='situations')

urlpatterns = [
    path('situations/', include(router.urls)),
    path('situations/current/', views.situation_current, name='situation_current'),
    path('situations/history/', views.situation_history, name='situation_history'),
    path('situations/me/', views.my_situation, name='my_situation'),
]






