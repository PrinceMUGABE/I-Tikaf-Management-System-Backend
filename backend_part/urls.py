
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('userApp.urls')),
    path('activity/', include('activityApp.urls')),
    path('resources/', include('resourceApp.urls')),
    path('activity-participants/', include('activityParticipantApp.urls')),
    path('feedback/', include('feedbacksApp.urls')),
    path('analytic/', include('analyticApp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)