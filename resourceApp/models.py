# resourcesApp/models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from activityApp.models import Activity
from userApp.models import CustomUser
import logging

logger = logging.getLogger(__name__)

class Resource(models.Model):
    name = models.CharField(max_length=100)
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_resources'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'

    def __str__(self):
        return f"{self.name} for {self.activity.name}"

    def clean(self):
        logger.info(f"Validating resource: {self.name}")
        
        # Validate name
        if not self.name or len(self.name.strip()) < 2:
            error_msg = 'Resource name must be at least 2 characters long.'
            logger.error(f"Resource validation failed - Name: {error_msg}")
            raise ValidationError({'name': error_msg})

        # Validate activity is active
        if not self.activity.is_active:
            error_msg = 'Cannot add resources to inactive activities.'
            logger.error(f"Resource validation failed - Activity: {error_msg}")
            raise ValidationError({'activity': error_msg})

        logger.info("Resource validation passed")

    def save(self, *args, **kwargs):
        logger.info(f"Saving resource: {self.name}")
        try:
            self.full_clean()
            super().save(*args, **kwargs)
            logger.info(f"Resource saved successfully - ID: {self.pk}")
        except ValidationError as e:
            logger.error(f"Resource save failed - Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Resource save failed - Unexpected error: {str(e)}", exc_info=True)
            raise