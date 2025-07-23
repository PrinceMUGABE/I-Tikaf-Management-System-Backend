# resourcesApp/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Resource
from .serializers import ResourceSerializer
from activityApp.models import Activity
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_resource(request):
    """
    Create a new resource for an activity
    Permissions: Authenticated users
    """
    logger.info(f"Creating resource - Request data: {request.data}")
    logger.info(f"Request user: {request.user} (ID: {request.user.id})")
    
    serializer = ResourceSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        logger.error(f"Resource creation failed - Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        resource = serializer.save(created_by=request.user)
        logger.info(f"Resource created successfully - ID: {resource.id}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Resource creation failed - Unexpected error: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred while creating the resource'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_resources(request):
    """
    Get all active resources (public access)
    """
    print("Listing all active resources")
    try:
        resources = Resource.objects.filter(is_active=True).order_by('-created_at')
        serializer = ResourceSerializer(resources, many=True)
        print(f"Found {resources.count()} active resources")
        return Response(serializer.data)
    except Exception as e:
        print(f"Error listing resources: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching resources'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def activity_resources(request, activity_id):
    """
    Get resources for a specific activity (public access)
    """
    logger.info(f"Fetching resources for activity ID: {activity_id}")
    try:
        activity = get_object_or_404(Activity, pk=activity_id, is_active=True)
        resources = Resource.objects.filter(activity=activity, is_active=True)
        serializer = ResourceSerializer(resources, many=True)
        logger.info(f"Found {resources.count()} resources for activity {activity_id}")
        return Response({
            'activity_id': activity_id,
            'activity_name': activity.name,
            'resources': serializer.data
        })
    except Activity.DoesNotExist:
        logger.warning(f"Activity not found - ID: {activity_id}")
        return Response(
            {'error': 'Activity not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error fetching activity resources: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching activity resources'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def resource_detail(request, pk):
    """
    Retrieve, update or delete a resource
    Permissions:
    - GET: Any authenticated user
    - PUT/PATCH/DELETE: Resource creator or admin
    """
    logger.info(f"Resource detail operation - ID: {pk}")
    logger.info(f"Request user: {request.user} (ID: {request.user.id})")
    
    try:
        resource = get_object_or_404(Resource, pk=pk, is_active=True)
        
        if request.method == 'GET':
            serializer = ResourceSerializer(resource)
            logger.info(f"Resource retrieved successfully - ID: {pk}")
            return Response(serializer.data)
        
        # Check permissions for write operations
        if not (request.user == resource.created_by or request.user.is_staff):
            logger.warning(
                f"Permission denied - User {request.user.id} tried to modify resource {pk} "
                f"created by {resource.created_by.id if resource.created_by else 'unknown'}"
            )
            return Response(
                {"detail": "Only resource creator or admin can modify resources."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method in ['PUT', 'PATCH']:
            serializer = ResourceSerializer(
                resource, 
                data=request.data, 
                partial=request.method == 'PATCH',
                context={'request': request}
            )
            
            if not serializer.is_valid():
                logger.error(f"Resource update failed - Validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            logger.info(f"Resource updated successfully - ID: {pk}")
            return Response(serializer.data)
        
        elif request.method == 'DELETE':
            resource.is_active = False
            resource.save()
            logger.info(f"Resource deactivated successfully - ID: {pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    except Resource.DoesNotExist:
        logger.warning(f"Resource not found - ID: {pk}")
        return Response(
            {'error': 'Resource not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in resource detail operation - ID: {pk}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while processing the resource'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_resources(request):
    """
    Get resources created by the current user
    """
    logger.info(f"Fetching resources for user - ID: {request.user.id}")
    
    try:
        resources = Resource.objects.filter(
            created_by=request.user,
            is_active=True
        ).order_by('-created_at')
        
        serializer = ResourceSerializer(resources, many=True)
        logger.info(f"Found {resources.count()} resources for user {request.user.id}")
        return Response({
            'count': resources.count(),
            'resources': serializer.data
        })
    except Exception as e:
        logger.error(f"Error fetching user resources: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching your resources'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )