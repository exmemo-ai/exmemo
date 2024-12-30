#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from loguru import logger

def init_django():
    """执行初始化命令"""
    from django.core.management import execute_from_command_line
    try:
        execute_from_command_line([sys.argv[0], "compilemessages"])
        execute_from_command_line([sys.argv[0], "makemigrations"])
        execute_from_command_line([sys.argv[0], "migrate"])
    except Exception as e:
        logger.warning(f'初始化失败: {e}')

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        if not os.environ.get('RUN_MAIN'):
            init_django()
    
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
