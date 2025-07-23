from django.urls import path
from .views import (
    user_analytics,
    activity_analytics,
    participation_analytics,
    feedback_analytics,
    resource_analytics,
    system_overview
)

urlpatterns = [
    path('users/', user_analytics, name='user-analytics'),
    path('activities/', activity_analytics, name='activity-analytics'),
    path('participations/', participation_analytics, name='participation-analytics'),
    path('feedbacks/', feedback_analytics, name='feedback-analytics'),
    path('resources/', resource_analytics, name='resource-analytics'),
    path('overview/', system_overview, name='system-overview'),
]