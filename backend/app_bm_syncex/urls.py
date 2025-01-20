from django.urls import path
from .views import BookmarkAPIView, BookmarkClickAPIView

urlpatterns = [
    path('', BookmarkAPIView.as_view(), name='bookmark'),
    path('click/', BookmarkClickAPIView.as_view(), name='bookmark-click-api'),
]
