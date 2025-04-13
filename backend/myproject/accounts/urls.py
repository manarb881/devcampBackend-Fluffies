
from django.urls import path
from .views import CurrentUserView, RegisterView, LoginView,ProfilePictureUploadView
from .views import MessageCreateView,MessageListView
urlpatterns = [
    path('me/', CurrentUserView.as_view(), name='current-user'),  # Current user endpoint
    path('register/', RegisterView.as_view(), name='register'),  # Register endpoint
    path('login/', LoginView.as_view(), name='login'),  # Custom login view
    path('profile-pic/', ProfilePictureUploadView.as_view(), name='login'), 
    path('messages/', MessageCreateView.as_view(), name='message-create'),
    path('messages/list', MessageListView.as_view(), name='message-list'),




]


