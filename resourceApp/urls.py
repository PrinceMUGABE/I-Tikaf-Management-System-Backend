# resourcesApp/urls.py
from django.urls import path
from .views import (
    create_resource,
    list_resources,
    activity_resources,
    resource_detail,
    user_resources,
)

app_name = 'resources'

urlpatterns = [
    # Resource CRUD endpoints
    path('', list_resources, name='list-resources'),
    path('create/', create_resource, name='create-resource'),
    path('<int:pk>/', resource_detail, name='resource-detail'),
    
    # Activity-specific resources
    path('activity/<int:activity_id>/', activity_resources, name='activity-resources'),
    
    # User-specific resources
    path('user/', user_resources, name='user-resources'),
]