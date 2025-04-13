# Imports related to DRF views and permissions
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Message
# Django imports
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

# Local imports for serializers and models
from .serializers import UserSerializer, CreateUserSerializer, MessageSerializer, UserProfileSerializer
from .models import UserProfile

# -----------------------------
# View for the Current User
# -----------------------------
class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# View for User Registration
# -----------------------------
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CreateUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            # Return validation errors
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


# -----------------------------
# View for User Login
# -----------------------------
class LoginView(APIView):
    # Override permission_classes to allow all (even if DEFAULT_PERMISSION_CLASSES requires authentication)
    permission_classes = []

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'detail': 'Username and password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Authenticate using the provided username and password
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        # Get or create an authentication token for the user
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


# -----------------------------
from rest_framework.permissions import IsAuthenticated

class ProfilePictureUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        profile_pic = request.FILES.get('profile_pic')
        
        if not profile_pic:
            return Response({"error": "No profile picture provided."}, status=status.HTTP_400_BAD_REQUEST)

        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.profile_pic = profile_pic
        user_profile.save()

        return Response({"message": "Profile picture updated successfully!"}, status=status.HTTP_200_OK)

# -----------------------------
# View for Message Creation
# -----------------------------
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import MessageSerializer
from rest_framework.permissions import IsAdminUser
class MessageCreateView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access

    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Message sent successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class MessageListView(APIView):
    permission_classes = [IsAdminUser]  # Only admins can access this

    def get(self, request):
        messages = Message.objects.all()  # Get all messages
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
