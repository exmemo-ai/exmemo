from django.urls import path
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app_translate.views import (
    TranslateAPIView,
    StoreWordViewSet,
    StoreArticleViewSet,
    TranslateAssistantView,
    TranslateLearnView
)

router = DefaultRouter()
router.register("word", StoreWordViewSet)
router.register("article", StoreArticleViewSet)

urlpatterns = [
    path("translate", TranslateAPIView.as_view(), name="translate-api"),
    path("learn", TranslateLearnView.as_view(), name="translate-learn"),
    path("assistant", TranslateAssistantView.as_view(), name="translate-assistant"),
    path("", include(router.urls), name="translate-data"),
]
