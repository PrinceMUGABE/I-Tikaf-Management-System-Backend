# activityParticipantApp/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.timezone import now
from django.db.models import Q

from .models import ActivityParticipant
from .serializers import (
    ActivityParticipantCreateSerializer,
    ActivityParticipantDetailSerializer,
    ActivityParticipantListSerializer,
    ActivityParticipantUpdateSerializer,
    ActivityStatisticsSerializer
)
from activityApp.models import Activity
from userApp.models import CustomUser


def handle_validation_error(error):
    """Helper function to format validation errors"""
    if isinstance(error, DjangoValidationError):
        if hasattr(error, 'message_dict'):
            return error.message_dict
        else:
            return {'detail': str(error)}
    return {'detail': str(error)}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_activity_participant(request):
    """Create a new activity participant"""
    try:
        print("Creating activity participant with data:", request.data,  "\nUser:", request.user)
        with transaction.atomic():
            serializer = ActivityParticipantCreateSerializer(data=request.data)
            if serializer.is_valid():
                participant = serializer.save()
                response_serializer = ActivityParticipantDetailSerializer(participant)
                return Response({
                    'success': True,
                    'message': 'Activity registration successful',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                print(f"\n Validation Failed {serializer.errors}\n")
                return Response({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
    except DjangoValidationError as e:
        print(f"Registration Failed:\t {handle_validation_error}\n")
        return Response({
            
            'success': False,
            'message': 'Registration failed',
            'errors': handle_validation_error(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"An exepected error occures: \t {e}\n")
        return Response({
            'success': False,
            'message': 'An unexpected error occurred',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_activity_participants(request):
    """Get all activity participants with filtering"""
    try:
        # Get query parameters
        search = request.GET.get('search', '')
        activity_id = request.GET.get('activity_id', '')
        status_filter = request.GET.get('status', '')
        
        # Base queryset
        queryset = ActivityParticipant.objects.filter(is_active=True).select_related(
            'activity', 'user'
        )
        
        # Apply filters
        if activity_id:
            queryset = queryset.filter(activity_id=activity_id)
        
        if status_filter:
            queryset = queryset.filter(participation_status=status_filter)
        
        if search:
            # Search in participant names or activity names
            queryset = queryset.filter(
                Q(user__christian_profile__first_name__icontains=search) |
                Q(user__christian_profile__last_name__icontains=search) |
                Q(user__ministry_leader_profile__first_name__icontains=search) |
                Q(user__ministry_leader_profile__last_name__icontains=search) |
                Q(activity__name__icontains=search)
            )
        
        # Get all participants without pagination
        participants = queryset.order_by('-created_at')
        serializer = ActivityParticipantListSerializer(participants, many=True)
        
        print(f"\n Retrieved participants: \t{serializer.data}\n")
        
        return Response({
            'success': True,
            'message': 'Activity participants retrieved successfully',
            'data': {
                'participants': serializer.data,
                'count': participants.count()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An unexpected error occurred',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_participant_by_id(request, participant_id):
    """Get a specific activity participant by ID"""
    try:
        participant = get_object_or_404(
            ActivityParticipant.objects.select_related('activity', 'user'),
            id=participant_id,
            is_active=True
        )
        
        serializer = ActivityParticipantDetailSerializer(participant)
        return Response({
            'success': True,
            'message': 'Activity participant retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Activity participant not found',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_activity_participant(request, participant_id):
    """Update an activity participant"""
    try:
        participant = get_object_or_404(
            ActivityParticipant,
            id=participant_id,
            is_active=True
        )
        
        with transaction.atomic():
            serializer = ActivityParticipantUpdateSerializer(
                participant, 
                data=request.data, 
                partial=request.method == 'PATCH'
            )
            
            if serializer.is_valid():
                updated_participant = serializer.save()
                response_serializer = ActivityParticipantDetailSerializer(updated_participant)
                return Response({
                    'success': True,
                    'message': 'Activity participant updated successfully',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except DjangoValidationError as e:
        return Response({
            'success': False,
            'message': 'Update failed',
            'errors': handle_validation_error(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An unexpected error occurred',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_activity_participant(request, participant_id):
    """Delete (soft delete) an activity participant"""
    try:
        participant = get_object_or_404(
            ActivityParticipant,
            id=participant_id,
            is_active=True
        )
        
        # Check if participant can be deleted (business logic)
        if participant.participation_status == 'attended':
            return Response({
                'success': False,
                'message': 'Cannot delete participant who has already attended the activity',
                'errors': {'detail': 'Cannot delete attended participant'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            participant.is_active = False
            participant.save()
            
        return Response({
            'success': True,
            'message': 'Activity participant deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An unexpected error occurred',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_activity_participations(request):
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
        print(f"Retrieved {queryset.count()} participations for user {user.id}")
        print("Serialized data:", serializer.data)
        
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_participants(request, activity_id):
    """Get all participants for a specific activity"""
    try:
        activity = get_object_or_404(Activity, id=activity_id, is_active=True)
        
        # Get query parameters
        status_filter = request.GET.get('status', '')
        include_stats = request.GET.get('include_stats', 'false').lower() == 'true'
        
        # Base queryset
        queryset = ActivityParticipant.objects.filter(
            activity=activity,
            is_active=True
        ).select_related('user', 'user__christian_profile', 'user__ministry_leader_profile')
        
        # Apply status filter
        if status_filter:
            queryset = queryset.filter(participation_status=status_filter)
        
        serializer = ActivityParticipantListSerializer(queryset, many=True)
        
        response_data = {
            'participants': serializer.data,
            'count': queryset.count()
        }
        
        # Include statistics if requested
        if include_stats:
            stats = ActivityParticipant.get_activity_statistics(activity)
            stats_serializer = ActivityStatisticsSerializer(stats)
            response_data['statistics'] = stats_serializer.data
        
        return Response({
            'success': True,
            'message': 'Activity participants retrieved successfully',
            'data': response_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An unexpected error occurred',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_participation_stats(request, activity_id):
    """Get participation statistics for a specific activity"""
    try:
        activity = get_object_or_404(Activity, id=activity_id, is_active=True)
        
        stats = ActivityParticipant.get_activity_statistics(activity)
        serializer = ActivityStatisticsSerializer(stats)
        
        return Response({
            'success': True,
            'message': 'Activity statistics retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while fetching statistics',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_participation_status(request):
    """Bulk update participation status for multiple participants"""
    try:
        user = request.user
        data = request.data
        
        # Validate required fields
        if not isinstance(data, list):
            return Response({
                'success': False,
                'message': 'Expected a list of participant updates',
                'errors': {'detail': 'Invalid input format'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not data:
            return Response({
                'success': False,
                'message': 'No participants provided for update',
                'errors': {'detail': 'Empty update list'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            updated_participants = []
            errors = []
            
            for idx, item in enumerate(data):
                try:
                    participant_id = item.get('participant_id')
                    new_status = item.get('participation_status')
                    
                    if not participant_id or not new_status:
                        errors.append({
                            'index': idx,
                            'error': 'Both participant_id and participation_status are required'
                        })
                        continue
                    
                    participant = get_object_or_404(
                        ActivityParticipant,
                        id=participant_id,
                        is_active=True
                    )
                    
                    # Verify user has permission to update (activity creator)
                    if participant.activity.created_by != user:
                        errors.append({
                            'index': idx,
                            'participant_id': participant_id,
                            'error': 'Insufficient permissions to update this participant'
                        })
                        continue
                    
                    # Validate status transition
                    old_status = participant.participation_status
                    valid_transitions = {
                        'registered': ['attended', 'cancelled', 'no_show'],
                        'attended': [],
                        'cancelled': ['registered'],
                        'no_show': ['registered']
                    }
                    
                    if new_status not in valid_transitions.get(old_status, []):
                        errors.append({
                            'index': idx,
                            'participant_id': participant_id,
                            'error': f'Invalid status transition from {old_status} to {new_status}'
                        })
                        continue
                    
                    # Additional business rules
                    if new_status == 'attended' and not participant.can_attend:
                        errors.append({
                            'index': idx,
                            'participant_id': participant_id,
                            'error': 'Cannot mark as attended (activity may not have started or already ended)'
                        })
                        continue
                    
                    if new_status == 'cancelled' and not participant.can_cancel:
                        errors.append({
                            'index': idx,
                            'participant_id': participant_id,
                            'error': 'Cannot cancel registration (activity may have already started)'
                        })
                        continue
                    
                    # Update participant
                    participant.participation_status = new_status
                    participant.save()
                    updated_participants.append(participant_id)
                    
                except Exception as e:
                    errors.append({
                        'index': idx,
                        'participant_id': participant_id if 'participant_id' in locals() else None,
                        'error': str(e)
                    })
            
            if errors:
                # If any errors occurred, roll back all changes
                transaction.set_rollback(True)
                return Response({
                    'success': False,
                    'message': 'Some updates failed',
                    'data': {
                        'successful_updates': updated_participants,
                        'errors': errors
                    }
                }, status=status.HTTP_207_MULTI_STATUS)
            
            return Response({
                'success': True,
                'message': f'Successfully updated {len(updated_participants)} participants',
                'data': {
                    'updated_participants': updated_participants
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An unexpected error occurred during bulk update',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_activity_participation(request, activity_id):
    """Check if the current user is registered for an activity and get participation details"""
    try:
        user = request.user
        activity = get_object_or_404(Activity, id=activity_id, is_active=True)
        
        try:
            participation = ActivityParticipant.objects.get(
                user=user,
                activity=activity,
                is_active=True
            )
            serializer = ActivityParticipantDetailSerializer(participation)
            
            return Response({
                'success': True,
                'message': 'Participation details found',
                'data': {
                    'is_registered': True,
                    'participation_details': serializer.data
                }
            }, status=status.HTTP_200_OK)
            
        except ActivityParticipant.DoesNotExist:
            return Response({
                'success': True,
                'message': 'User is not registered for this activity',
                'data': {
                    'is_registered': False,
                    'participation_details': None
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while checking participation',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        
        
        
        
        
from django.utils.timezone import now  
from django.utils import timezone   
        
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_as_attended(request, participant_id):
    """
    Mark a participant's status as 'attended'
    Only allowed if:
    - Current user is activity organizer or admin
    - Participant is currently 'registered'
    - Current time is within activity timeframe
    """
    try:
        participant = get_object_or_404(
            ActivityParticipant,
            id=participant_id,
            is_active=True
        )

        # Authorization check
        if not (request.user == participant.user or request.user.role != "imam"):
            print("You don't have permission to perform this action.")
            return Response(
                {"detail": "You don't have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Business logic validation
        if participant.participation_status != 'registered':
            print(f"Can only mark 'registered' participants as attended. Current status: {participant.participation_status}")
            return Response(
                {"detail": f"Can only mark 'registered' participants as attended. Current status: {participant.participation_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_time = timezone.now()
        if not (participant.activity.start_datetime <= current_time <= participant.activity.end_datetime):
            print("Can only mark attendance during the activity timeframe")
            return Response(
                {"detail": "Can only mark attendance during the activity timeframe"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        participant.participation_status = 'attended'
        participant.save()

        # Return updated participant data
        serializer = ActivityParticipantDetailSerializer(participant)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error marking participant as attended: {str(e)}")
        return Response(
            {"detail": "An error occurred while processing your request"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )