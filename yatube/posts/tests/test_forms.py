import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(author=cls.user,
                                       text='Тестовый текст',
                                       group=cls.group)
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.form_data = {
            'text': 'Тестовый текст',
            'group.id': 'Тестовая группа',
            'image': uploaded,
        }
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.expected_post = 'Пост отредактирован гостем'

    def test_create_post(self):
        """Валидная форма создаёт запись в Post."""
        posts_count = Post.objects.count()
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            id=1,
            image=self.post.image
        ).exists())

    def test_edit_post(self):
        """Валидная форма меняет запись в Post."""
        self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=self.form_data,
            follow=True
        )
        self.post.save()
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, self.post.text)
        self.assertTrue(Post.objects.filter(id=1).exists())

    def test_guest_user_post_edit(self):
        """Отправка формы редактирования неавторизованным пользователем
        не меняет данные в базе."""
        form_data = {
            'text': 'Пост отредактирован гостем',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        post = Post.objects.get(id=1)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )
        self.assertNotEqual(post.text, self.expected_post)

    def test_add_comment_authorized_client(self):
        """После успешной отправки комментарий появляется на странице поста
        (авторизованным пользователем)."""
        comments_count = Comment.objects.count()
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=self.form_data,
            follow=True)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(id=1).exists())

    def test_add_comment_guest_client(self):
        """После успешной отправки комментарий не появляется на странице поста
        (неавторизованным пользователем)."""
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=self.form_data,
            follow=True)
        self.assertFalse(Comment.objects.filter(id=1).exists())
