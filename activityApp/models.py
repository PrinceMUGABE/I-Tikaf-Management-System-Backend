from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from userApp.models import CustomUser
import logging

logger = logging.getLogger(__name__)

class Activity(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    description = models.TextField()
    image = models.ImageField(upload_to='activity_images/', blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='activities_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    required_participants = models.PositiveIntegerField(default=1)
    current_participants = models.PositiveIntegerField(default=0)
    
    # Removed ManyToManyField - use ActivityParticipant model directly

    class Meta:
        ordering = ['-start_datetime']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'

    def __str__(self):
        return self.name

    def clean(self):
        logger.info(f"Cleaning activity: {self.name}")

        # Validate name
        if not self.name or len(self.name.strip()) < 3:
            error_msg = 'Activity name must be at least 3 characters long.'
            logger.error(f"Activity validation failed - Name: {error_msg}")
            raise ValidationError({'name': error_msg})

        # Validate date/time
        if self.start_datetime >= self.end_datetime:
            error_msg = 'End datetime must be after start datetime.'
            logger.error(f"Activity validation failed - Datetime: {error_msg}")
            logger.debug(f"Start: {self.start_datetime}, End: {self.end_datetime}")
            raise ValidationError({'end_datetime': error_msg})

        # Validate participants count
        if self.required_participants < 1:
            error_msg = 'Required participants must be at least 1.'
            logger.error(f"Activity validation failed - Participants: {error_msg}")
            raise ValidationError({'required_participants': error_msg})

        # Check for overlapping activities
        overlapping_activities = Activity.objects.filter(
            models.Q(start_datetime__lt=self.end_datetime) &
            models.Q(end_datetime__gt=self.start_datetime),
            is_active=True
        ).exclude(pk=self.pk if self.pk else None)

        if overlapping_activities.exists():
            error_msg = 'There is already an activity scheduled during the specified time.'
            logger.error(f"Activity validation failed - Overlap: {error_msg}")
            logger.debug(f"Overlapping activities: {list(overlapping_activities.values_list('id', 'name'))}")
            raise ValidationError(error_msg)

        logger.info("Activity validation passed")

    def save(self, *args, **kwargs):
        logger.info(f"Saving activity: {self.name}")
        try:
            self.full_clean()
            super().save(*args, **kwargs)
            logger.info(f"Activity saved successfully - ID: {self.pk}")
        except ValidationError as e:
            logger.error(f"Activity save failed - Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Activity save failed - Unexpected error: {str(e)}", exc_info=True)
            raise

    # Helper methods using the reverse relationship from ActivityParticipant
    def get_registered_participants(self):
        """Get all registered participants for this activity"""
        return self.participants.filter(
            participation_status='registered',
            is_active=True
        )
    
    def get_attended_participants(self):
        """Get all participants who attended this activity"""
        return self.participants.filter(
            participation_status='attended',
            is_active=True
        )
    
    def get_participant_count(self):
        """Get current registered participant count (legacy method - kept for compatibility)"""
        return self.participants.filter(
            participation_status='registered',
            is_active=True
        ).count()
    
    def get_registered_count(self):
        """Get current registered participant count"""
        return self.participants.filter(
            participation_status='registered',
            is_active=True
        ).count()
    
    def get_available_spots(self):
        """Get number of available spots remaining"""
        return max(0, self.required_participants - self.get_registered_count())
    
    def is_full(self):
        """Check if activity has reached maximum participants"""
        return self.get_registered_count() >= self.required_participants
    
    def can_register(self):
        """Check if new registrations are allowed"""
        return (
            self.is_active and
            not self.is_full() and
            self.start_datetime > timezone.now()
        )
    
    def get_participation_statistics(self):
        """Get detailed participation statistics"""
        from activityParticipantApp.models import ActivityParticipant
        stats = ActivityParticipant.get_activity_statistics(self)
        stats['available_spots'] = self.get_available_spots()
        stats['is_full'] = self.is_full()
        return stats