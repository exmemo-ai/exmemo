from django.apps import AppConfig
from loguru import logger
from django.db import connections, OperationalError


class AppDataforgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_dataforge"

    def ready(self):
        logger.info("App init")
        self.create_database_if_not_exists()

    def create_database_if_not_exists(self):
        db_settings = connections.databases["default"]
        db_name = db_settings["NAME"]

        try:
            connection = connections["default"]
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        except OperationalError:
            self.create_database(db_name)
        try:
            connection = connections["default"]
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        except OperationalError:
            logger.warning(f"connect {db_name} failed")

    def create_database(self, db_name):
        logger.info(f"Creating database {db_name}")
        connection = connections["postgres"]
        connection.ensure_connection()

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{db_name}';")
            exists = cursor.fetchone()

            if not exists:
                cursor.execute(f"CREATE DATABASE {db_name};")
                print(f"Database {db_name} created successfully.")
