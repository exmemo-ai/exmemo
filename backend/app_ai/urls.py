from django.urls import path, include
from app_ai.views import StorePromptViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("prompt", StorePromptViewSet)

urlpatterns = [path("", include(router.urls), name="prompt-api"),]
