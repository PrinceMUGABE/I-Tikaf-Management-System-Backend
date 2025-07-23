from django.forms import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Activity
from .serializers import ActivitySerializer
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_activity(request):
    """
    Create a new activity.
    Permissions: 
    - Authenticated users (with additional role checks if needed)
    """
    logger.info(f"Creating activity - Request data: {request.data}")
    logger.info(f"Request user: {request.user} (ID: {request.user.id})")
    
    serializer = ActivitySerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        logger.error(f"Activity creation failed - Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        activity = serializer.save(created_by=request.user)
        logger.info(f"Activity created successfully - ID: {activity.id}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        logger.error(f"Activity creation failed - Validation error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Activity creation failed - Unexpected error: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred while creating the activity'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_activities(request):
    """
    Get all active activities (public access)
    """
    logger.info("Listing all active activities")
    try:
        activities = Activity.objects.filter(is_active=True).order_by('start_datetime')
        serializer = ActivitySerializer(activities, many=True)
        logger.info(f"Found {activities.count()} active activities")
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error listing activities: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching activities'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def activity_detail(request, pk):
    """
    Get activity details by ID (public access)
    """
    logger.info(f"Fetching activity details for ID: {pk}")
    try:
        activity = get_object_or_404(Activity, pk=pk, is_active=True)
        serializer = ActivitySerializer(activity)
        logger.info(f"Successfully fetched activity ID: {pk}")
        return Response(serializer.data)
    except Activity.DoesNotExist:
        logger.warning(f"Activity not found - ID: {pk}")
        return Response(
            {'error': 'Activity not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error fetching activity details - ID: {pk}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching activity details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_activity(request, pk):
    """
    Update activity details.
    Permissions:
    - Activity creator
    - Admin
    """
    logger.info(f"Updating activity - ID: {pk}")
    logger.info(f"Request user: {request.user} (ID: {request.user.id})")
    logger.debug(f"Request data: {request.data}")
    
    try:
        activity = get_object_or_404(Activity, pk=pk, is_active=True)
        
        # Check permissions
        if not (request.user == activity.created_by or request.user.is_staff):
            logger.warning(
                f"Permission denied - User {request.user.id} tried to update activity {pk} "
                f"created by {activity.created_by.id}"
            )
            return Response(
                {"detail": "Only activity creator or admin can update activities."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ActivitySerializer(
            activity, 
            data=request.data, 
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        
        if not serializer.is_valid():
            logger.error(f"Activity update failed - Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        logger.info(f"Activity updated successfully - ID: {pk}")
        return Response(serializer.data)
    
    except Activity.DoesNotExist:
        logger.warning(f"Activity not found - ID: {pk}")
        return Response(
            {'error': 'Activity not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error updating activity - ID: {pk}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while updating the activity'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_activity(request, pk):
    """
    Delete (deactivate) an activity.
    Permissions:
    - Activity creator
    - Admin
    """
    logger.info(f"Deleting activity - ID: {pk}")
    logger.info(f"Request user: {request.user} (ID: {request.user.id})")
    
    try:
        activity = get_object_or_404(Activity, pk=pk, is_active=True)
        
        # Check permissions
        if not (request.user == activity.created_by or request.user.is_staff):
            logger.warning(
                f"Permission denied - User {request.user.id} tried to delete activity {pk} "
                f"created by {activity.created_by.id}"
            )
            return Response(
                {"detail": "Only activity creator or admin can delete activities."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        activity.is_active = False
        activity.save()
        logger.info(f"Activity deactivated successfully - ID: {pk}")
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    except Activity.DoesNotExist:
        logger.warning(f"Activity not found - ID: {pk}")
        return Response(
            {'error': 'Activity not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error deleting activity - ID: {pk}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while deleting the activity'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activities(request):
    """
    Get activities created by the current user
    """
    logger.info(f"Fetching activities for user - ID: {request.user.id}")
    
    try:
        activities = Activity.objects.filter(
            created_by=request.user,
            is_active=True
        ).order_by('-start_datetime')
        
        serializer = ActivitySerializer(activities, many=True)
        logger.info(f"Found {activities.count()} activities for user {request.user.id}")
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error fetching user activities - User ID: {request.user.id}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching your activities'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        
        
        
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import Activity
from .serializers import ActivitySerializer
from userApp.models import CustomUser
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_itikaf_activities(request):
    """
    Retrieve I'tikaf activities for authenticated users
    """
    logger.info(f"Fetching I'tikaf activities for user {request.user.id}")
    
    try:
        # Check if user is eligible for I'tikaf activities
        if not hasattr(request.user, 'itikaf_profile') or not request.user.itikaf_profile.is_active:
            logger.warning(
                f"User {request.user.id} doesn't have an active I'tikaf profile"
            )
            return Response(
                {
                    'error': 'I\'tikaf profile not found',
                    'message': 'You must have an active I\'tikaf profile to view these activities.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get query parameters
        upcoming_only = request.GET.get('upcoming', 'false').lower() == 'true'
        days_ahead = int(request.GET.get('days', 30))
        active_only = request.GET.get('active_only', 'true').lower() == 'true'
        
        # Base queryset - I'tikaf activities
        activities = Activity.objects.filter(
            location__icontains="mosque",  # Filter for mosque activities
            is_active=True
        )
        
        # Filter by active status
        if active_only:
            activities = activities.filter(is_active=True)
        
        # Filter for upcoming activities
        if upcoming_only:
            now = timezone.now()
            future_date = now + timedelta(days=days_ahead)
            activities = activities.filter(
                start_datetime__gte=now,
                start_datetime__lte=future_date
            )
        
        # Order by start datetime
        activities = activities.order_by('start_datetime')
        
        # Serialize the activities
        serializer = ActivitySerializer(activities, many=True)
        
        logger.info(f"Retrieved {activities.count()} I'tikaf activities for user {request.user.id}")
        
        # Prepare response data
        response_data = {
            'count': activities.count(),
            'itikaf_profile': {
                'id': request.user.itikaf_profile.id,
                'status': request.user.itikaf_profile.get_status_display(),
            },
            'activities': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching I'tikaf activities: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching I\'tikaf activities'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_itikaf_schedule(request):
    """
    Get the complete I'tikaf schedule for the current period
    """
    logger.info(f"Fetching I'tikaf schedule for user {request.user.id}")
    
    try:
        # Check if user is eligible
        if not hasattr(request.user, 'itikaf_profile') or not request.user.itikaf_profile.is_active:
            logger.warning(
                f"User {request.user.id} doesn't have an active I'tikaf profile"
            )
            return Response(
                {
                    'error': 'I\'tikaf profile not found',
                    'message': 'You must have an active I\'tikaf profile to view the schedule.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all I'tikaf activities for the current period
        now = timezone.now()
        ramadan_end = now + timedelta(days=30)  # Adjust based on actual Ramadan period
        
        activities = Activity.objects.filter(
            location__icontains="mosque",
            is_active=True,
            start_datetime__gte=now,
            end_datetime__lte=ramadan_end
        ).order_by('start_datetime')
        
        serializer = ActivitySerializer(activities, many=True)
        
        logger.info(f"Retrieved {activities.count()} I'tikaf schedule items for user {request.user.id}")
        
        return Response({
            'period_start': now.date(),
            'period_end': ramadan_end.date(),
            'total_activities': activities.count(),
            'schedule': serializer.data
        })
    
    except Exception as e:
        logger.error(f"Error fetching I'tikaf schedule: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching I\'tikaf schedule'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )