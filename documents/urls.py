# documents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, ContentTypeViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'contenttypes', ContentTypeViewSet, basename='contenttype')




from . import views_pages as pages

urlpatterns = [
    path('documents/', include(router.urls)),
    path("documents/list/", pages.documents_page, name="document_list"),
    path("documents/my/", pages.documents_my_page, name="document_my"),
]

