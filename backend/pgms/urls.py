from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT auth
    path('api/auth/login/',   LoginView.as_view(),        name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/',  LogoutView.as_view(),       name='token_blacklist'),

    # App routers
    path('api/accounts/',      include('accounts.urls',      namespace='accounts')),
    path('api/courses/',       include('courses.urls',       namespace='courses')),
    path('api/results/',       include('results.urls',       namespace='results')),
    path('api/fees/',          include('fees.urls',          namespace='fees')),
    path('api/reports/',       include('reports.urls',       namespace='reports')),
    path('api/notifications/', include('notifications.urls', namespace='notifications')),
]

if settings.DEBUG:
    # Only profile pictures are public. Course materials and fee receipts are
    # served through authenticated API views and must never be exposed here
    # (nor by the production web server).
    urlpatterns += static(settings.MEDIA_URL + 'profiles/', document_root=settings.MEDIA_ROOT / 'profiles')
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
