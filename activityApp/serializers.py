from rest_framework import serializers
from userApp.serializers import CustomUserSerializer
from .models import Activity
import logging
from django.db import models

logger = logging.getLogger(__name__)


class ActivitySerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    registered_count = serializers.SerializerMethodField()
    available_spots = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    
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
            'is_active',
            'required_participants',
            'registered_count',
            'available_spots',
            'is_full',
            'can_register',
            'attendance_rate'
        ]
        read_only_fields = [
            'created_by', 
            'created_at', 
            'updated_at'
        ]

    def get_registered_count(self, obj):
        """Get current registered participant count"""
        return obj.get_registered_count()

    def get_available_spots(self, obj):
        """Get number of available spots remaining"""
        return obj.get_available_spots()

    def get_is_full(self, obj):
        """Check if activity is full"""
        return obj.is_full()

    def get_can_register(self, obj):
        """Check if registration is still open"""
        return obj.can_register()
    
    def get_attendance_rate(self, obj):
        """Get attendance rate percentage for completed activities"""
        try:
            stats = obj.get_participation_statistics()
            total_registered = stats.get('total_registered', 0)
            total_attended = stats.get('total_attended', 0)
            
            if total_registered == 0:
                return 0.0
            
            return round((total_attended / total_registered) * 100, 2)
        except Exception:
            return 0.0

    def validate_name(self, value):
        if not value or len(value.strip()) < 3:
            error_msg = "Activity name must be at least 3 characters long."
            logger.error(f"Validation Error - Name: {error_msg}")
            raise serializers.ValidationError(error_msg)
        return value

    def validate_required_participants(self, value):
        if value < 1:
            error_msg = "Required participants must be at least 1."
            logger.error(f"Validation Error - Participants: {error_msg}")
            raise serializers.ValidationError(error_msg)
        return value

    def validate(self, data):
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
                    models.Q(start_datetime__lt=end_datetime) &
                    models.Q(end_datetime__gt=start_datetime),
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