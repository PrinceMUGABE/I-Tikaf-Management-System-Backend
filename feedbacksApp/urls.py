# activityFeedbackApp/urls.py (New URL patterns)
from django.urls import path
from . import views

urlpatterns = [
    # User feedback management
    path('my-attended-activities/', views.get_user_attended_activities, name='user_attended_activities'),
    path('create/', views.create_feedback, name='create_feedback'),
    path('my-feedbacks/', views.list_user_feedbacks, name='user_feedbacks'),
    path('update/<int:feedback_id>/', views.update_feedback, name='update_feedback'),
    path('delete/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),
    
    # Activity feedback viewing
    path('activity/<int:activity_id>/', views.list_activity_feedbacks, name='activity_feedbacks'),
]