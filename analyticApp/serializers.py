from rest_framework import serializers
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from userApp.models import CustomUser
from activityApp.models import Activity
from resourceApp.models import Resource
from activityParticipantApp.models import ActivityParticipant
from feedbacksApp.models import ActivityFeedback

class BaseAnalyticsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    today = serializers.IntegerField()
    this_week = serializers.IntegerField()
    this_month = serializers.IntegerField()
    
    def get_queryset(self, model):
        queryset = model.objects.all()
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        
        return {
            'total': queryset.count(),
            'today': queryset.filter(created_at__date=today).count(),
            'this_week': queryset.filter(created_at__date__gte=start_of_week).count(),
            'this_month': queryset.filter(created_at__date__gte=start_of_month).count(),
        }

class UserAnalyticsSerializer(BaseAnalyticsSerializer):
    by_role = serializers.DictField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    
    def get_queryset(self, model):
        base_data = super().get_queryset(model)
        queryset = model.objects.all()
        
        # Get counts by role
        role_counts = dict(queryset.values_list('role').annotate(count=Count('role')))
        
        # Get active/inactive counts
        active_users = queryset.filter(is_active=True).count()
        inactive_users = queryset.filter(is_active=False).count()
        
        return {
            **base_data,
            'by_role': role_counts,
            'active_users': active_users,
            'inactive_users': inactive_users,
        }

class ActivityAnalyticsSerializer(BaseAnalyticsSerializer):
    upcoming = serializers.IntegerField()
    ongoing = serializers.IntegerField()
    completed = serializers.IntegerField()
    avg_participants = serializers.FloatField()
    avg_resources = serializers.FloatField()
    
    def get_queryset(self, model):
        base_data = super().get_queryset(model)
        queryset = model.objects.all()
        now = timezone.now()
        
        # Get activity status counts
        upcoming = queryset.filter(start_datetime__gt=now).count()
        ongoing = queryset.filter(start_datetime__lte=now, end_datetime__gte=now).count()
        completed = queryset.filter(end_datetime__lt=now).count()
        
        # Calculate average participants per activity
        avg_participants = queryset.annotate(
            participant_count=Count('participants')
        ).aggregate(avg=Avg('participant_count'))['avg'] or 0
        
        # Calculate average resources per activity
        avg_resources = queryset.annotate(
            resource_count=Count('resources')
        ).aggregate(avg=Avg('resource_count'))['avg'] or 0
        
        return {
            **base_data,
            'upcoming': upcoming,
            'ongoing': ongoing,
            'completed': completed,
            'avg_participants': round(avg_participants, 1),
            'avg_resources': round(avg_resources, 1),
        }

class ParticipationAnalyticsSerializer(BaseAnalyticsSerializer):
    by_status = serializers.DictField()
    attendance_rate = serializers.FloatField()
    
    def get_queryset(self, model):
        base_data = super().get_queryset(model)
        queryset = model.objects.all()
        
        # Get counts by participation status
        status_counts = dict(queryset.values_list('participation_status').annotate(count=Count('participation_status')))
        
        # Calculate attendance rate
        total_participations = queryset.count()
        attended = queryset.filter(participation_status='attended').count()
        attendance_rate = (attended / total_participations * 100) if total_participations > 0 else 0
        
        return {
            **base_data,
            'by_status': status_counts,
            'attendance_rate': round(attendance_rate, 1),
        }

class FeedbackAnalyticsSerializer(BaseAnalyticsSerializer):
    avg_rating = serializers.FloatField()
    rating_distribution = serializers.DictField()
    feedback_ratio = serializers.FloatField()
    
    def get_queryset(self, model):
        base_data = super().get_queryset(model)
        queryset = model.objects.all()
        
        # Calculate average rating
        avg_rating = queryset.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Get rating distribution
        rating_distribution = dict(queryset.values_list('rating').annotate(count=Count('rating')))
        
        # Calculate feedback ratio (feedback per activity)
        total_activities = Activity.objects.count()
        feedback_ratio = (queryset.count() / total_activities) if total_activities > 0 else 0
        
        return {
            **base_data,
            'avg_rating': round(avg_rating, 1),
            'rating_distribution': rating_distribution,
            'feedback_ratio': round(feedback_ratio, 1),
        }

class ResourceAnalyticsSerializer(BaseAnalyticsSerializer):
    by_activity = serializers.DictField()
    avg_per_activity = serializers.FloatField()
    
    def get_queryset(self, model):
        base_data = super().get_queryset(model)
        queryset = model.objects.all()
        
        # Get top 5 activities with most resources
        by_activity = dict(queryset.values_list('activity__name').annotate(
            count=Count('activity')
        ).order_by('-count')[:5])
        
        # Calculate average resources per activity
        total_activities = Activity.objects.count()
        avg_per_activity = (queryset.count() / total_activities) if total_activities > 0 else 0
        
        return {
            **base_data,
            'by_activity': by_activity,
            'avg_per_activity': round(avg_per_activity, 1),
        }