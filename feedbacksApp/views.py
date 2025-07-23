from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import ActivityFeedback
from .serializers import ActivityFeedbackSerializer, FeedbackCreateSerializer
from activityApp.models import Activity
from activityParticipantApp.models import ActivityParticipant
from django.utils.timezone import now
from django.db import transaction
from activityParticipantApp.serializers import ActivityParticipantListSerializer
from userApp.models import CustomUser

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_feedback(request):
    """
    Create new feedback for an activity
    Validations:
    - User must be authenticated
    - Activity must exist
    - User must have attended the activity
    - User must not have already provided feedback
    - Rating must be between 1-5
    """
    print(f"\n submitted data: {request.data}\n")
    serializer = FeedbackCreateSerializer(data=request.data)
    if not serializer.is_valid():
        print(f"\n Error: {serializer.errors}\n")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    activity_id = request.data.get('activity')  # Get activity ID directly from request data
    user = request.user  # request.user is already the user object
    
    print("User: ", user.phone_number)
    
    # Validate activity exists
    try:
        activity = Activity.objects.get(id=activity_id, is_active=True)
        print("Found activity: ", activity.name)
    except Activity.DoesNotExist:
        print("Activity not found")
        return Response(
            {"error": "Activity not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    

    # Validate no existing feedback
    if ActivityFeedback.objects.filter(created_by=user, activity=activity).exists():
        print("You have already provided feedback for this activity")
        return Response(
            {"error": "You have already provided feedback for this activity"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate rating
    rating = serializer.validated_data['rating']
    if not 1 <= rating <= 5:
        print("Rating must be between 1 and 5")
        return Response(
            {"error": "Rating must be between 1 and 5"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create feedback
    feedback = ActivityFeedback.objects.create(
        created_by=user,
        activity=activity,
        rating=rating,
        comment=serializer.validated_data.get('comment')
    )
    
    return Response(
        ActivityFeedbackSerializer(feedback, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )
    
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def update_feedback(request, feedback_id):
    """
    Update existing feedback
    Validations:
    - User must own the feedback
    - Rating must be between 1-5
    """
    feedback = get_object_or_404(ActivityFeedback, id=feedback_id)
    
    # Validate ownership
    if feedback.created_by != request.user:
        return Response(
            {"error": "You can only update your own feedback"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = FeedbackCreateSerializer(feedback, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate rating if provided
    if 'rating' in serializer.validated_data:
        rating = serializer.validated_data['rating']
        if not 1 <= rating <= 5:
            return Response(
                {"error": "Rating must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Update feedback
    serializer.save()
    
    return Response(
        ActivityFeedbackSerializer(feedback, context={'request': request}).data,
        status=status.HTTP_200_OK
    )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def delete_feedback(request, feedback_id):
    """
    Delete feedback
    Validations:
    - User must own the feedback
    """
    feedback = get_object_or_404(ActivityFeedback, id=feedback_id)
    
    # Validate ownership
    if feedback.created_by != request.user:
        return Response(
            {"error": "You can only delete your own feedback"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    feedback.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_feedbacks(request):
    """
    List all feedbacks by the current user
    """
    feedbacks = ActivityFeedback.objects.filter(
        created_by=request.user
    ).select_related('activity', 'created_by').order_by('-created_at')
    
    serializer = ActivityFeedbackSerializer(feedbacks, many=True)
    return Response({
        'count': feedbacks.count(),
        'results': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_activity_feedbacks(request, activity_id):
    """
    List all feedbacks for an activity
    Validations:
    - User must be creator or attendee of the activity
    """
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Validate permissions
    is_creator = activity.created_by == request.user
    is_attendee = ActivityParticipant.objects.filter(
        activity=activity,
        user=request.user,
        participation_status='attended'
    ).exists()
    
    if not (is_creator or is_attendee or request.user.is_staff):
        return Response(
            {"error": "You don't have permission to view these feedbacks"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    feedbacks = ActivityFeedback.objects.filter(
        activity=activity
    ).select_related('created_by').order_by('-created_at')
    
    serializer = ActivityFeedbackSerializer(feedbacks, many=True)
    return Response({
        'activity': {
            'id': activity.id,
            'name': activity.name
        },
        'count': feedbacks.count(),
        'results': serializer.data
    })




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_attended_activities(request):
    """Get activity participations for the logged-in user"""
    try:
        user = request.user
        
        # Get query parameters
        status_filter = request.GET.get('status', '')
        upcoming_only = request.GET.get('upcoming_only', 'false').lower() == 'true'
        
        # Base queryset with optimizations
        queryset = ActivityParticipant.objects.filter(
            user=user,
            is_active=True
        ).select_related(
            'activity',
            'user'
        ).order_by('-created_at')
        
        # Apply filters
        if status_filter:
            queryset = queryset.filter(participation_status=status_filter)
        
        if upcoming_only:
            queryset = queryset.filter(activity__start_datetime__gt=now())
        
        serializer = ActivityParticipantListSerializer(queryset, many=True)
        # print(f"Retrieved {queryset.count()} participations for user {user.id}")
        # print("Serialized data:", serializer.data)
        
        return Response({
            'success': True,
            'message': 'User activity participations retrieved successfully',
            'data': {
                'participations': serializer.data,
                'count': queryset.count()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error fetching user participations: {str(e)}")
        return Response({
            'success': False,
            'message': 'An unexpected error occurred',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
