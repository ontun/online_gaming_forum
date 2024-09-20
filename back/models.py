import uuid

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, default="all")

    def __str__(self):
        return self.name


class Advertisement(models.Model):
    CATEGORY_CHOICES = [
        ('Tanks', 'Танки'),
        ('Heal', 'Хилы'),
        ('DD', 'ДД'),
        ('Merchants', 'Торговцы'),
        ('Guild_masters', 'Гилдмастеры'),
        ('Quest_givers', 'Квестгиверы'),
        ('Blacksmiths', 'Кузнецы'),
        ('Tanners', 'Кожевники'),
        ('Potion_makers', 'Зельевары'),
        ('Spell_masters', 'Мастера заклинаний'),
    ]

    title = models.CharField(max_length=100)
    content = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='advertisements')
    images = models.ImageField(upload_to='advertisement_images/', null=True, blank=True)
    video_file = models.FileField(upload_to='advertisement_videos/', null=True, blank=True)

    def get_absolute_url(self):
        return reverse('advertisement_detail', args=[self.id])

    def __str__(self):
        return self.title


class Response(models.Model):
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Response to '{self.advertisement.title}' by {self.user.username}"


class ConfirmationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Confirmation code for {self.user.username}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscribe_to_news = models.BooleanField(default=False)

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'
