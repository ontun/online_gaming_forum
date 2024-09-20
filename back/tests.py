'''

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from .models import Advertisement
import os


class AdvertisementModelTest(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(username='testuser', password='12345')

        # Пути к тестовым файлам
        self.image_path = os.path.join(os.path.dirname(__file__), '..', 'test_image.jpg')
        self.video_path = os.path.join(os.path.dirname(__file__), '..', 'test_video.mp4')

    def test_advertisement_creation_with_image_and_video(self):
        # Открываем тестовые файлы
        with open(self.image_path, 'rb') as img_file, open(self.video_path, 'rb') as vid_file:
            image = SimpleUploadedFile(name='test_image.jpg', content=img_file.read(), content_type='image/jpeg')
            video = SimpleUploadedFile(name='test_video.mp4', content=vid_file.read(), content_type='video/mp4')

            # Создаем объявление с изображением и видео
            ad = Advertisement.objects.create(
                title='Test Title',
                content='Test Content',
                images=image,
                category='Tanks',
                video_file=video,
                user=self.user
            )

            # Проверяем, что объявление создано и файлы сохранены
            self.assertEqual(ad.title, 'Test Title')
            self.assertEqual(ad.content, 'Test Content')
            self.assertTrue(ad.images.name.endswith('test_image.jpg'))
            self.assertTrue(ad.video_file.name.endswith('test_video.mp4'))
            self.assertEqual(ad.user, self.user)

    def test_advertisement_creation_without_image_and_video(self):
        # Создаем объявление без изображения и видео
        ad = Advertisement.objects.create(
            title='Test Title',
            content='Test Content',
            category='Tanks',
            user=self.user
        )

        # Проверяем, что объявление создано без файлов
        self.assertEqual(ad.title, 'Test Title')
        self.assertEqual(ad.content, 'Test Content')
        self.assertFalse(ad.images)  # Проверяем, что поле пустое
        self.assertFalse(ad.video_file)  # Проверяем, что поле пустое
        self.assertEqual(ad.user, self.user)'''

