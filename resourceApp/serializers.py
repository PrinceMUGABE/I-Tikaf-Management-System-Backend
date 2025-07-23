# resourcesApp/serializers.py
from rest_framework import serializers
from .models import Resource
from activityApp.serializers import ActivitySerializer
from userApp.serializers import CustomUserSerializer
import logging
from .models import Activity

logger = logging.getLogger(__name__)

class ResourceSerializer(serializers.ModelSerializer):
    activity = ActivitySerializer(read_only=True)
    activity_id = serializers.PrimaryKeyRelatedField(
        queryset=Activity.objects.filter(is_active=True),
        source='activity',
        write_only=True
    )
    created_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = Resource
        fields = [
            'id',
            'name',
            'activity',
            'activity_id',
            'description',
            'created_at',
            'created_by',
            'is_active'
        ]
        read_only_fields = ['created_at', 'created_by']

    def validate_name(self, value):
        if not value or len(value.strip()) < 2:
            error_msg = "Resource name must be at least 2 characters long."
            logger.error(f"Validation Error - Name: {error_msg}")
            raise serializers.ValidationError(error_msg)
        return value

    def validate(self, data):
        logger.info("Starting resource validation")
        
        # Validate activity is active
        activity = data.get('activity')
        if activity and not activity.is_active:
            error_msg = "Cannot add resources to inactive activities."
            logger.error(f"Validation Error - Activity: {error_msg}")
            raise serializers.ValidationError({'activity': error_msg})
        
        logger.info("Resource validation completed successfully")
        return data