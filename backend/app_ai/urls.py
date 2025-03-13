from django.urls import path, include
from app_ai.views import StorePromptViewSet, QAAPIView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("prompt", StorePromptViewSet)

urlpatterns = [path("", include(router.urls), name="prompt-api"),
            path("qa/", QAAPIView.as_view(), name="qa-api"),
]
