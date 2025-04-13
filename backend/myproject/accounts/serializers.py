from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Message

# Serializer for User Profile
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'city', 'state', 'postal_code', 'country', 'is_admin','profile_pic']

# Serializer for User (used for updating user details)
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)  # Optional profile

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']
        read_only_fields = ['id']  # ID is read-only

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})  # Extract profile data
        instance = super().update(instance, validated_data)  # Update user details
        
        # Update profile if provided
        if profile_data:
            # If profile exists, update it; if not, create new profile
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance

# Serializer for Creating User (with password confirmation)
class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name']
    
    def validate(self, attrs):
        # Validate password confirmation
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Validate email uniqueness
        if not attrs['email']:
            raise serializers.ValidationError({"email": "Email is required."})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already in use."})
        
        return attrs
    
    def create(self, validated_data):
        # Remove the password confirmation field before creating user
        validated_data.pop('password2')
        
        # Create user with password
        user = User.objects.create_user(**validated_data)

        # Optionally create a UserProfile if needed
        # If you want to create a profile for every user, uncomment the following:
        # UserProfile.objects.create(user=user) 

        return user

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['username', 'email', 'message']