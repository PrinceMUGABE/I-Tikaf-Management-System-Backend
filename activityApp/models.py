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

        # Check for overlapping activities
        overlapping_activities = Activity.objects.filter(
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
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