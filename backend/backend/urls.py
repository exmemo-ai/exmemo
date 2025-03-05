from django.contrib import admin
from django.urls import path, include
from backend.common.user.views import UserAPIView, SettingAPIView, LoginView
from backend.common.utils.sys_tools import is_app_installed
from app_paper.views import PaperAPIView
from app_web.views import WebAPIView
from knox import views as knox_views

urlpatterns = [
    path("api/entry/", include("app_dataforge.urls")),
    path("api/message/", include("app_message.urls")),
    #
    path("api/ai/", include("app_ai.urls")),
    path("api/web/", WebAPIView.as_view(), name="web-api"),
    path("api/paper/", PaperAPIView.as_view(), name="paper-api"),
    #
    path("api/bookmarks/", include("app_bm_syncex.urls")),
    path("api/keeper/", include("app_bm_keeper.urls")),
    #
    path("api/sync/", include("app_sync.urls")),
    #
    path("api/user/", UserAPIView.as_view(), name="user-api"),
    path("api/setting/", SettingAPIView.as_view(), name="setting-api"),
    #
    path(r"api/auth/login/", LoginView.as_view(), name="knox_login"),
    path(r"api/auth/logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path(
        r"api/auth/logoutall/",
        knox_views.LogoutAllView.as_view(),
        name="knox_logoutall",
    ),
    #
    path("admin/", admin.site.urls),
]

if is_app_installed("app_translate"):
    urlpatterns.append(path("api/translate/", include("app_translate.urls")))

if is_app_installed("app_record"):
    from app_record.views import RecordAPIView

    urlpatterns.append(path("api/record/", RecordAPIView.as_view(), name="record-api"))
