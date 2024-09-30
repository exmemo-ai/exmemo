from django.urls import path
from app_sync.views import SyncAPIView

urlpatterns = [path("", SyncAPIView.as_view(), name="sync-api")]
