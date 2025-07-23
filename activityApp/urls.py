from django.urls import path
from .views import (
    create_activity,
    list_activities,
    activity_detail,
    update_activity,
    delete_activity,
    user_activities,
    get_itikaf_activities,
    get_itikaf_schedule,
)

urlpatterns = [
    path('activities/', list_activities, name='list-activities'),
    path('activities/create/', create_activity, name='create-activity'),
    path('activities/<int:pk>/', activity_detail, name='activity-detail'),
    path('activities/<int:pk>/update/', update_activity, name='update-activity'),
    path('activities/<int:pk>/delete/', delete_activity, name='delete-activity'),
    
    path('user/activities/', user_activities, name='user-activities'),
    
    path('itikaf/activities/', get_itikaf_activities, name='itikaf-activities'),
    path('itikaf/schedule/', get_itikaf_schedule, name='itikaf-schedule'),
]