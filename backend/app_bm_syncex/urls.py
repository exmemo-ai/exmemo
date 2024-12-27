from django.urls import path
from .views import BookmarkAPIView, BookmarkClickAPIView
# from .views import BookmarkSettingsView

urlpatterns = [
    path('', BookmarkAPIView.as_view(), name='bookmark'),
    path('click/', BookmarkClickAPIView.as_view(), name='bookmark-click'),
    # path('settings/', BookmarkSettingsView.as_view(), name='bookmark-settings'),
]
