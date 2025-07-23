from rest_framework import serializers
from .models import CustomUser
from django.core.mail import send_mail



from django.contrib.auth import authenticate
from rest_framework import serializers

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'phone_number', 'email', 'role', 'created_at']


class ContactUsSerializer(serializers.Serializer):
    names = serializers.CharField(max_length=100, required=True)
    email = serializers.EmailField(required=True)
    subject = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)