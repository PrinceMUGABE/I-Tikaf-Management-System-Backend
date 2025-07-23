from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from activityApp.models import Activity

User = get_user_model()

class ActivityFeedback(models.Model):
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="feedbacks"
    )
    activity = models.ForeignKey(
        Activity, 
        on_delete=models.CASCADE, 
        related_name="feedbacks"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['created_by', 'activity']
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback by {self.created_by} for {self.activity}"