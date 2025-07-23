# activityParticipantApp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Activity Participant CRUD Operations
    path('create/', views.create_activity_participant, name='create_activity_participant'),
    path('all/', views.get_all_activity_participants, name='get_all_activity_participants'),
    path('<int:participant_id>/', views.get_activity_participant_by_id, name='get_activity_participant_by_id'),
    path('update/<int:participant_id>/', views.update_activity_participant, name='update_activity_participant'),
    path('delete/<int:participant_id>/', views.delete_activity_participant, name='delete_activity_participant'),
    
    # User-specific activity participations
    path('my-participations/', views.get_user_activity_participations, name='get_user_activity_participations'),
    
    # Activity-specific participants
    path('participants/<int:activity_id>/', views.get_activity_participants, name='get_activity_participants'),
    path('stats/<int:activity_id>/', views.get_activity_participation_stats, name='get_activity_participation_stats'),
    path('check-participation/<int:activity_id>/', views.check_user_activity_participation, name='check_user_activity_participation'),
    
    # Bulk operations
    path('bulk-update-status/', views.bulk_update_participation_status, name='bulk_update_participation_status'),
    path('mark-attended/<int:participant_id>/', views.mark_as_attended, name='update_activity_participant'),
]