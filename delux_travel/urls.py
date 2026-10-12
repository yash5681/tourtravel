from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

# Custom Admin Site Branding
admin.site.site_header = "Delux Tour & Travel Management"
admin.site.site_title = "Delux Admin Portal"
admin.site.index_title = "Welcome to Delux Travel Portal"

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('tours.urls')),
]

# Static assets resolution: serves both /static/... and root /style.css, /app.js, etc.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        re_path(r'^(?P<path>.*\.(?:css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf))$',
                serve, {'document_root': settings.STATICFILES_DIRS[0]}),
    ]
