from django.urls import path
from app_message.views import MessageAPIView, SessionAPIView

urlpatterns = [
    path("", MessageAPIView.as_view(), name="message-api"),
    path("session/", SessionAPIView.as_view(), name="session-api"),
]