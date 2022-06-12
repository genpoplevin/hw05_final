from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class StatusURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )

    def setUp(self):
        self.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        self.urls_anonymous_user = [
            '/',
            f'/group/{self.group.slug}/',
            f'/posts/{self.post.id}/',
            f'/profile/{self.user}/',
            '/about/author/',
            '/about/tech/',
        ]
        self.template_404 = 'core/404.html'
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_exists_uses_correct_template(self):
        """Все URL-адреса доступны и используют соответствующий шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_all_pages_exists_at_disired_location(self):
        """Все страницы доступны авторизованному пользователю."""
        for url in self.templates_url_names.keys():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_anonymous_user_exists_at_desired_location(self):
        """Страницы из списка urls_anonymous_user в SetUp классе доступны
           неавторизованному пользователю."""
        for url in self.urls_anonymous_user:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous_on_auth_login(self):
        """
        Страница по адресу /posts/post_id/edit/ доступна и перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """
        Страница по адресу /create/ доступна и перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернет ошибку 404
           и при этом будет использован кастомный шаблон."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, self.template_404)
