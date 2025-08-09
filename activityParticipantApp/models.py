from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from userApp.models import CustomUser
from activityApp.models import Activity
import logging

logger = logging.getLogger(__name__)

class ActivityParticipant(models.Model):
    PARTICIPATION_STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('attended', 'Attended'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show')
    ]

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='activity_participations'
    )
    participation_status = models.CharField(
        max_length=20,
        choices=PARTICIPATION_STATUS_CHOICES,
        default='registered'
    )
    registration_date = models.DateTimeField(default=now)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Activity Participant'
        verbose_name_plural = 'Activity Participants'
        ordering = ['-created_at']
        # Remove unique_together constraint to allow re-registration
        # unique_together = ['activity', 'user']  # Comment out or remove this line
        indexes = [
            models.Index(fields=['activity', 'participation_status']),
            models.Index(fields=['user', 'registration_date']),
            models.Index(fields=['activity', 'user', 'participation_status']),  # Add this for better querying
        ]

    def __str__(self):
        user_name = getattr(self.user, 'christian_profile', None)
        if user_name:
            display_name = f"{user_name.first_name} {user_name.last_name}"
        elif hasattr(self.user, 'ministry_leader_profile'):
            leader = self.user.ministry_leader_profile
            display_name = f"{leader.first_name} {leader.last_name}"
        else:
            display_name = self.user.phone_number
        
        return f"{display_name} - {self.activity.name}"

    def clean(self):
        """Validate the activity participation"""
        errors = {}

        # Check if activity exists and is active
        if not self.activity:
            errors['activity'] = 'Activity is required.'
        elif not self.activity.is_active:
            errors['activity'] = 'Cannot register for inactive activities.'

        # Check if user exists and is active
        if not self.user:
            errors['user'] = 'User is required.'
        elif not self.user.is_active:
            errors['user'] = 'Cannot register inactive users for activities.'

        # Validate user role - only participants and imams can participate
        if self.user and self.user.role not in ['imam', 'participant']:
            errors['user'] = 'Only Participants and Imam can participate in activities.'

        # Check if activity registration is still open
        if self.activity and self.activity.start_datetime <= now():
            if self.participation_status == 'registered' and not self.pk:  # New registration
                errors['activity'] = 'Cannot register for activities that have already started.'

        # Check for existing active registration (business logic constraint)
        if self.activity and self.user and not self.pk:  # New registration
            existing_registration = ActivityParticipant.objects.filter(
                activity=self.activity,
                user=self.user,
                participation_status__in=['registered', 'attended'],  # Active statuses
                is_active=True
            ).first()
            
            if existing_registration:
                if existing_registration.participation_status == 'registered':
                    errors['non_field_errors'] = 'User is already registered for this activity.'
                elif existing_registration.participation_status == 'attended':
                    errors['non_field_errors'] = 'User has already attended this activity.'

        # Validate participation status transitions for updates
        if self.pk:  # Existing record
            try:
                old_instance = ActivityParticipant.objects.get(pk=self.pk)
                # Define valid status transitions
                valid_transitions = {
                    'registered': ['attended', 'cancelled', 'no_show'],
                    'attended': [],  # Cannot change from attended
                    'cancelled': ['registered'],  # Can re-register
                    'no_show': ['registered']  # Can re-register
                }
                
                if (old_instance.participation_status != self.participation_status and 
                    self.participation_status not in valid_transitions.get(old_instance.participation_status, [])):
                    errors['participation_status'] = f'Cannot change status from {old_instance.participation_status} to {self.participation_status}.'
            except ActivityParticipant.DoesNotExist:
                pass

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Save with validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def participant_name(self):
        """Get participant's full name"""
        if hasattr(self.user, 'christian_profile'):
            profile = self.user.christian_profile
            return f"{profile.first_name} {profile.last_name}"
        elif hasattr(self.user, 'ministry_leader_profile'):
            profile = self.user.ministry_leader_profile
            return f"{profile.first_name} {profile.last_name}"
        return self.user.phone_number

    @property
    def participant_role(self):
        """Get participant's role"""
        return self.user.get_role_display()

    @property
    def can_cancel(self):
        """Check if participation can be cancelled"""
        return (self.participation_status == 'registered' and 
                self.activity.start_datetime > now())

    @property
    def can_attend(self):
        """Check if participation status can be marked as attended"""
        return (self.participation_status == 'registered' and 
                self.activity.start_datetime <= now() <= self.activity.end_datetime)

    @classmethod
    def get_user_upcoming_activities(cls, user):
        """Get upcoming activities for a user"""
        return cls.objects.filter(
            user=user,
            participation_status='registered',
            activity__start_datetime__gt=now(),
            activity__is_active=True,
            is_active=True
        ).select_related('activity')

    @classmethod
    def get_activity_statistics(cls, activity):
        """Get participation statistics for an activity"""
        participants = cls.objects.filter(activity=activity, is_active=True)
        return {
            'total_registered': participants.filter(participation_status='registered').count(),
            'total_attended': participants.filter(participation_status='attended').count(),
            'total_cancelled': participants.filter(participation_status='cancelled').count(),
            'total_no_show': participants.filter(participation_status='no_show').count(),
            'total_participants': participants.count()
        }