import os
import pytz
from datetime import datetime
from django.conf import settings
from tzlocal import get_localzone

def get_current_time():
    now = datetime.now()
    seconds = now.timestamp()
    return int(seconds)


def is_app_installed(app_name):
    return app_name in settings.INSTALLED_APPS

def get_timezone():
    timezone = os.getenv('TIMEZONE', None)
    if timezone:
        return pytz.timezone(timezone)
    local_timezone = get_localzone()
    return pytz.timezone(str(local_timezone))
