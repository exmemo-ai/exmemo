from datetime import datetime
from django.conf import settings


def get_current_time():
    now = datetime.now()
    seconds = now.timestamp()
    return int(seconds)


def is_app_installed(app_name):
    return app_name in settings.INSTALLED_APPS
