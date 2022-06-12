from django.conf import settings
from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_object_post_name = self.post.text[
            :settings.FIRST_FIFTEEN_CHARS
        ]
        expected_object_group_name = self.group.title
        self.assertEqual(expected_object_post_name, str(self.post))
        self.assertEqual(expected_object_group_name, str(self.group))
        self.assertIsInstance(expected_object_post_name, str)
        self.assertIsInstance(expected_object_group_name, str)
