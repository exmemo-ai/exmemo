from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
from django.urls import path, include
from .views import StoreEntryViewSet, EntryAPIView

router = DefaultRouter()
router.register("data", StoreEntryViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("docs/", include_docs_urls(title="API document")),
    path("tool/", EntryAPIView.as_view(), name="entry-tool"),
]
