import os

from celery import Celery


# ------------------------------------------------------------
# Django settings
# ------------------------------------------------------------

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


# ------------------------------------------------------------
# Celery application
# ------------------------------------------------------------

app = Celery(
    "wp_api"
)


# ------------------------------------------------------------
# Load configuration from Django settings
# ------------------------------------------------------------

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)


# ------------------------------------------------------------
# Automatically discover tasks.py
# ------------------------------------------------------------

app.autodiscover_tasks()