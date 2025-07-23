from rest_framework import serializers
from .models import ActivityFeedback
from activityApp.serializers import ActivitySerializer
from userApp.serializers import CustomUserSerializer

class ActivityFeedbackSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    activity = ActivitySerializer(read_only=True)
    
    class Meta:
        model = ActivityFeedback
        fields = [
            'id', 'created_by', 'activity', 
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'activity', 'created_at', 'updated_at']

class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityFeedback
        fields = ['activity', 'rating', 'comment']
        extra_kwargs = {
            'activity': {'write_only': True},
            'rating': {'required': True},
            'comment': {'required': False}
        }