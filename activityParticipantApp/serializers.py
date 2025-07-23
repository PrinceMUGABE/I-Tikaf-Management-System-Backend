# activityParticipantApp/serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.timezone import now
from .models import ActivityParticipant
from activityApp.models import Activity
from userApp.models import CustomUser
from userApp.serializers import CustomUserSerializer
from activityApp.serializers import ActivitySerializer

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'phone_number', 'email', 'role', 'created_at']


class ActivitySerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Activity
        fields = [
            'id',
            'name',
            'title',
            'location',
            'start_datetime',
            'end_datetime',
            'description',
            'image',
            'created_by',
            'created_at',
            'updated_at',
            'is_active'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']



class ActivityParticipantListSerializer(serializers.ModelSerializer):
    """Serializer for listing activity participants with basic details"""
    participant = CustomUserSerializer(source='user', read_only=True)  # Map 'participant' to 'user'
    activity = ActivitySerializer(read_only=True)
    activity_date = serializers.DateTimeField(source='activity.start_datetime', read_only=True)
    participation_status_display = serializers.CharField(source='get_participation_status_display', read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    can_attend = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ActivityParticipant
        fields = [
            'id', 'participant', 'activity', 
            'activity_date', 'participation_status', 'participation_status_display',
            'registration_date', 'can_cancel', 'can_attend', 'notes', 
            'created_at', 'is_active'
        ]
        read_only_fields = fields

class ActivityParticipantDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for activity participants with full related data"""
    activity = ActivitySerializer(read_only=True)
    user = CustomUserSerializer(read_only=True)
    participation_status_display = serializers.CharField(source='get_participation_status_display', read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    can_attend = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ActivityParticipant
        fields = [
            'id', 'activity', 'user',
            'participation_status', 'participation_status_display', 
            'registration_date', 'notes', 'can_cancel', 'can_attend',
            'created_at', 'updated_at', 'is_active'
        ]


class ActivityParticipantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating activity participants"""
    
    class Meta:
        model = ActivityParticipant
        fields = [
            'activity', 'user', 'participation_status', 'notes'
        ]
        extra_kwargs = {
            'participation_status': {'default': 'registered'},
            'notes': {'required': False, 'allow_blank': True}
        }

    def validate_activity(self, value):
        """Validate activity"""
        if not value.is_active:
            raise serializers.ValidationError("Cannot register for inactive activities.")
        
        if value.start_datetime <= now():
            raise serializers.ValidationError("Cannot register for activities that have already started.")
        
        return value

    def validate_user(self, value):
        """Validate user"""
        if not value.is_active:
            raise serializers.ValidationError("Cannot register inactive users for activities.")
        
        if value.role not in ['participant', 'imam']:
            raise serializers.ValidationError("Only particicpants and Imam can participate in activities.")
        
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        activity = attrs.get('activity')
        user = attrs.get('user')
        
        if activity and user:
            # Check if user already registered for this activity
            if ActivityParticipant.objects.filter(activity=activity, user=user, is_active=True).exists():
                raise serializers.ValidationError("User is already registered for this activity.")
        
        return attrs

    def create(self, validated_data):
        """Create activity participant with proper error handling"""
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            # Convert Django validation errors to DRF format
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            else:
                raise serializers.ValidationError(str(e))


class ActivityParticipantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating activity participants"""
    
    class Meta:
        model = ActivityParticipant
        fields = [
            'participation_status', 'notes'
        ]

    def validate_participation_status(self, value):
        """Validate status transitions"""
        if self.instance:
            old_status = self.instance.participation_status
            valid_transitions = {
                'registered': ['attended', 'cancelled', 'no_show'],
                'attended': [],  # Cannot change from attended
                'cancelled': ['registered'],  # Can re-register
                'no_show': ['registered']  # Can re-register
            }
            
            if old_status != value and value not in valid_transitions.get(old_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {old_status} to {value}."
                )
                
            # Additional business logic validation
            if value == 'attended' and not self.instance.can_attend:
                raise serializers.ValidationError(
                    "Cannot mark as attended. Activity may not have started yet or already ended."
                )
                
            if value == 'cancelled' and not self.instance.can_cancel:
                raise serializers.ValidationError(
                    "Cannot cancel registration. Activity may have already started."
                )
        
        return value

    def update(self, instance, validated_data):
        """Update with proper error handling"""
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            else:
                raise serializers.ValidationError(str(e))


class ActivityStatisticsSerializer(serializers.Serializer):
    """Serializer for activity participation statistics"""
    total_registered = serializers.IntegerField()
    total_attended = serializers.IntegerField()
    total_cancelled = serializers.IntegerField()
    total_no_show = serializers.IntegerField()
    total_participants = serializers.IntegerField()
    attendance_rate = serializers.SerializerMethodField()
    
    def get_attendance_rate(self, obj):
        """Calculate attendance rate"""
        total_registered = obj.get('total_registered', 0)
        total_attended = obj.get('total_attended', 0)
        
        if total_registered == 0:
            return 0.0
        
        return round((total_attended / total_registered) * 100, 2)