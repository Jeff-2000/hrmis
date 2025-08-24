"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),  # Assuming main.urls exists
    path('', include('authentication.urls')),
    path('api/v1/', include('employee.urls')),
    path('api/v1/', include('attendance.urls')),
    path('api/v1/', include('documents.urls')),
    path('api/v1/', include('notifications.urls')),
    path('api/v1/', include('payroll.urls')),
    path('api/v1/', include('leave.urls')),
    path('api/v1/', include('situation.urls')),
    path('api/v1/', include('audit.urls')),
    path('api/v1/', include('analytics.urls')),
    path('api/v1/', include('a_account.urls')),  # Updated to a_account
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # path("api/v1/integrations/", include(("integrations.urls", "integrations"), namespace="integrations")),
    path("api/v1/integrations/", include(("integrations.urls", "integrations"), namespace="integrations")),
]



# from django.contrib import admin
# from django.urls import path, include
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

# schema_view = get_schema_view(
#     openapi.Info(
#         title="HRMIS API",
#         default_version='v1',
#         description="API documentation for HRMIS",
#         contact=openapi.Contact(email="admin@fonctionpublique.ci"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=[permissions.AllowAny],
# )

# urlpatterns += [
#     path('openapi.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
#     path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
#     path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
# ]


# if settings.DEBUG:
#     # Include django_browser_reload URLs only in DEBUG mode
#     urlpatterns += [
#         path("__reload__/", include("django_browser_reload.urls")),
#     ]
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Optional: restrict docs in production to staff only
class DocsPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow freely in DEBUG; otherwise staff only (tweak as you prefer)
        return settings.DEBUG or (request.user and request.user.is_staff)

schema_view = get_schema_view(
    openapi.Info(
        title="Human Resources Management Information System API, by Jeff Pierre.",
        default_version="v1",
        description="API documentation for Human Resources Management Information System",
        contact=openapi.Contact(email="jeffpierre720@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(DocsPermission,),   #choice: DocsPermission or permissions.AllowAny
)

urlpatterns += [

    # --- Your three documentation routes ---
    path("openapi.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),

    # Optional: make / go to Swagger
    path("", RedirectView.as_view(url="/swagger/", permanent=False)),
]

# Static/media (dev only)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=getattr(settings, "STATIC_ROOT", None))
    urlpatterns += static(settings.MEDIA_URL, document_root=getattr(settings, "MEDIA_ROOT", None))

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

