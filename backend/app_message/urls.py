from django.urls import path
from app_message.views import MessageAPIView

urlpatterns = [path("", MessageAPIView.as_view(), name="message-api")]
