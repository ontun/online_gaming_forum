from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Advertisement, Category
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
import os
from pathlib import Path
from configparser import ConfigParser
import logging

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

config_file = os.path.join(BASE_DIR, 'email_config.ini')

# Создание парсера и чтение файла конфигурации
config = ConfigParser()
config.read(config_file)

email_host_user = config.get('email', 'EMAIL_HOST_USER') + '@yandex.ru'

logger = logging.getLogger(__name__)


@shared_task
def send_daily_advertisements():
    try:
        logger.info('Task started: send_daily_advertisements')

        # Вычисляем начало вчерашнего дня (00:00)
        yesterday = timezone.now() - timedelta(days=1)
        yesterday_start = timezone.make_aware(datetime(yesterday.year, yesterday.month, yesterday.day))
        logger.info(f'Calculated yesterday_start: {yesterday_start}')

        # Получаем объявления за последний день
        advertisements = Advertisement.objects.filter(created_at__gte=yesterday_start)
        logger.info(f'Retrieved advertisements: {list(advertisements)}')

        # Сортируем объявления по количеству откликов
        top_advertisements = sorted(advertisements, key=lambda ad: ad.responses.count(), reverse=True)[:10]
        logger.info(f'Sorted top advertisements: {list(top_advertisements)}')

        subject = 'Топ 10 объявлений за вчерашний день'
        content = 'Самые популярные объявления за вчерашний день:\n\n'

        if not top_advertisements:
            subject = '10 последних объявлений'
            content = '10 самых новых объявлений:\n\n'
            logger.info('No top advertisements found for the specified period.')
            # Получаем 10 последних объявлений, если не нашлось популярных
            top_advertisements = Advertisement.objects.order_by('-created_at')[:10]
            logger.info(f'Retrieved last 10 advertisements: {list(top_advertisements)}')

        for advertisement in top_advertisements:
            # Получаем категории объявления
            categories = advertisement.category
            # Добавляем ссылку на объявление в текст письма
            content += f"- <a href='{settings.SITE_URL}{reverse('advertisement_detail', args=[advertisement.id])}'>{advertisement.title}</a> ({categories})\n"
            # Добавлен код для создания URL
            advertisement.url = f"{settings.SITE_URL}{reverse('advertisement_detail', args=[advertisement.id])}"
        logger.info('Email content prepared')

        # Получаем email-адреса подписанных пользователей
        subscribed_users = User.objects.filter(
            profile__subscribe_to_news=True
        ).values_list('email', flat=True)
        logger.info(f'Retrieved subscribed users: {list(subscribed_users)}')

        if not subscribed_users:
            logger.info('No subscribed users found.')
            return

        # Проверка перед отправкой писем
        logger.info(f'Sending emails from: {settings.DEFAULT_FROM_EMAIL}')

        # Отправляем письма с помощью EmailMultiAlternatives
        for recipient in subscribed_users:
            print(recipient)
            html_content = render_to_string(
                'email/weekly_articles.html',
                {
                    'advertisements': top_advertisements,
                }
            )
            email = EmailMultiAlternatives(
                subject,
                content,
                settings.DEFAULT_FROM_EMAIL,
                [recipient]
            )
            email.attach_alternative(html_content, "text/html")  # добавляем html
            email.send(fail_silently=False)
            print("После отправки")
        logger.info('Emails sent successfully')
    except Exception as e:
        logger.error(f"Ошибка в задаче: {e}")
