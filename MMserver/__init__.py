from __future__ import absolute_import, unicode_literals

# Это гарантирует, что приложение всегда импортируется, когда Django запускается
# так что shared_task будет использовать это приложение.
from .celery import app as celery_app

__all__ = ('celery_app',)
