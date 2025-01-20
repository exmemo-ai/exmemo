from django.urls import path
from .views import BMKeeperAPIView
from .nav_custom_order import BookmarkCustomOrderAPIView

urlpatterns = [
    path('', BMKeeperAPIView.as_view(), name='keeper-api'),
    path('folders/', BMKeeperAPIView.as_view(), name='keeper-folders-api'),
    path("move/", BMKeeperAPIView.as_view(), name="keeper-move-api"),
    path('custom-order/', BookmarkCustomOrderAPIView.as_view(), name='keeper-custom-order-api'),
]