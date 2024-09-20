import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MMserver.settings')
app = Celery('MMserver')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Настройка расписания Celery Beat
app.conf.beat_schedule = {
    'send-newsletter-every-day-at-9am': {
        'task': 'back.tasks.send_daily_advertisements',
        'schedule': crontab(hour='9', minute='0'),  # Используй желаемое время
    },
}

app.conf.timezone = 'Europe/Moscow'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
