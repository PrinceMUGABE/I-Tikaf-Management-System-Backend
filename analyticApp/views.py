from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import (
    UserAnalyticsSerializer,
    ActivityAnalyticsSerializer,
    ParticipationAnalyticsSerializer,
    FeedbackAnalyticsSerializer,
    ResourceAnalyticsSerializer
)
from userApp.models import CustomUser
from activityApp.models import Activity
from activityParticipantApp.models import ActivityParticipant
from feedbacksApp.models import ActivityFeedback
from resourceApp.models import Resource

@api_view(['GET'])
def user_analytics(request):
    serializer = UserAnalyticsSerializer(data=UserAnalyticsSerializer().get_queryset(CustomUser))
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data)

@api_view(['GET'])
def activity_analytics(request):
    serializer = ActivityAnalyticsSerializer(data=ActivityAnalyticsSerializer().get_queryset(Activity))
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data)

@api_view(['GET'])
def participation_analytics(request):
    serializer = ParticipationAnalyticsSerializer(data=ParticipationAnalyticsSerializer().get_queryset(ActivityParticipant))
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data)

@api_view(['GET'])
def feedback_analytics(request):
    serializer = FeedbackAnalyticsSerializer(data=FeedbackAnalyticsSerializer().get_queryset(ActivityFeedback))
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data)

@api_view(['GET'])
def resource_analytics(request):
    serializer = ResourceAnalyticsSerializer(data=ResourceAnalyticsSerializer().get_queryset(Resource))
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data)

@api_view(['GET'])
def system_overview(request):
    analytics = {
        'users': UserAnalyticsSerializer().get_queryset(CustomUser),
        'activities': ActivityAnalyticsSerializer().get_queryset(Activity),
        'participations': ParticipationAnalyticsSerializer().get_queryset(ActivityParticipant),
        'feedbacks': FeedbackAnalyticsSerializer().get_queryset(ActivityFeedback),
        'resources': ResourceAnalyticsSerializer().get_queryset(Resource),
    }
    return Response(analytics)