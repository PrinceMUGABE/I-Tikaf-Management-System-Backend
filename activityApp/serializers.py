from rest_framework import serializers
from userApp.serializers import CustomUserSerializer
from .models import Activity
import logging

logger = logging.getLogger(__name__)

class ActivitySerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Activity
        fields = [
            'id',
            'name',
            'title',
            'location',
            'start_datetime',
            'end_datetime',
            'description',
            'image',
            'created_by',
            'created_at',
            'updated_at',
            'is_active'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate_name(self, value):
        if not value or len(value.strip()) < 3:
            error_msg = "Activity name must be at least 3 characters long."
            logger.error(f"Validation Error - Name: {error_msg}")
            raise serializers.ValidationError(error_msg)
        return value

    def validate(self, data):
        # Log validation start
        logger.info("Starting activity validation")
        
        # Check if end datetime is after start datetime
        if 'start_datetime' in data and 'end_datetime' in data:
            if data['start_datetime'] >= data['end_datetime']:
                error_msg = "End datetime must be after start datetime."
                logger.error(f"Validation Error - Datetime: {error_msg}")
                raise serializers.ValidationError(
                    {'end_datetime': error_msg}
                )
        
        # Check for overlapping activities
        if 'start_datetime' in data or 'end_datetime' in data:
            start_datetime = data.get('start_datetime', self.instance.start_datetime if self.instance else None)
            end_datetime = data.get('end_datetime', self.instance.end_datetime if self.instance else None)
            
            if start_datetime and end_datetime:
                overlapping_activities = Activity.objects.filter(
                    start_datetime__lt=end_datetime,
                    end_datetime__gt=start_datetime,
                    is_active=True
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if overlapping_activities.exists():
                    error_msg = "There is already an activity scheduled during the specified time."
                    logger.error(f"Validation Error - Overlap: {error_msg}")
                    logger.debug(f"Overlapping activities: {overlapping_activities.values_list('id', flat=True)}")
                    raise serializers.ValidationError(
                        {'non_field_errors': [error_msg]}
                    )
        
        logger.info("Activity validation completed successfully")
        return data