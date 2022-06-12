from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User


class PostPagesTest(TestCase):
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
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cache.clear()

    def setUp(self):
        self.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'auth'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        self.guest_client = Client()
        self.user = User.objects.create_user(username='author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user1 = User.objects.create_user(username='follower')
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.user2 = User.objects.create_user(username='notfollower')
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user1)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index__page_show_correct_context(self):
        """Шаблон index при запросе авторизованного пользователя сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author.username)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(post_image_0, self.post.image)

    def test_index_group_list_profile_page_show_correct_context(self):
        """Шаблоны index (при запросе неавторизованного пользователя),
        group_list, profile сформированы с правильным контекстом."""
        responses = [
            self.guest_client.get(reverse('posts:index')),
            self.authorized_client.get(
                reverse('posts:group_list',
                        kwargs={'slug': 'test-slug'})
            ),
            self.guest_client.get(
                reverse('posts:group_list',
                        kwargs={'slug': 'test-slug'})
            ),
            self.authorized_client.get(
                reverse('posts:profile',
                        kwargs={'username': 'auth'})
            ),
            self.guest_client.get(
                reverse('posts:profile',
                        kwargs={'username': 'auth'})
            ),
        ]
        for response in responses:
            with self.subTest(response=response):
                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author.username
                post_text_0 = first_object.text
                post_group_0 = first_object.group.title
                post_image_0 = first_object.image
                self.assertEqual(post_author_0, self.post.author.username)
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_group_0, self.group.title)
                self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        responses = [
            self.guest_client.
            get(
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
            self.authorized_client.
            get(
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            )
        ]
        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(response.context['post'].text, self.post.text)
                self.assertEqual(
                    response.context['post'].author.username,
                    self.post.author.username
                )
                self.assertEqual(
                    response.context['post'].image, self.post.image
                )

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_exist_index_group_list_profile(self):
        """При создании поста этот пост появляется на главной странице,
        странице с группами, странице профиля пользователя."""
        responses = [
            self.authorized_client.get(
                reverse('posts:index')
            ),
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ),
            self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': 'auth'})
            )
        ]
        for response in responses:
            with self.subTest(response=response):
                self.assertIn(
                    Post.objects.all()[0],
                    response.context['page_obj'])

    def test_post_not_in_another_group_page(self):
        """Пост не попадает в группу, для которой не был предназначен."""
        Group.objects.create(
            title='Тестовая группа',
            slug='test-any-slug',
            description='Тестовое описание',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-any-slug'})
        )
        self.assertNotIn(Post.objects.get(id=1), response.context['page_obj'])

    def test_index_page_cache_correct(self):
        """Кеш главной страницы работает правильно."""
        response = self.authorized_client.get(reverse('posts:index'))
        temp_post = Post.objects.get(id=1)
        temp_post.delete()
        new_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, new_response.content)
        cache.clear()
        new_new_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, new_new_response.content)

    def test_authorized_user_can_follow_unfollow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        author = self.user
        user = self.user1
        self.authorized_client1.get(
            reverse('posts:profile_follow',
                    kwargs={'username': author.username})
        )
        self.assertTrue(Follow.objects.filter(user=user,
                                              author=author).exists())
        self.authorized_client1.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': author.username})
        )
        self.assertFalse(Follow.objects.filter(user=user,
                                               author=author).exists())

    def test_post_appears_in_feed(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        author = self.user
        user1 = self.user1
        user2 = self.user2
        self.authorized_client1.get(
            reverse('posts:profile_follow',
                    kwargs={'username': author.username})
        )
        authors1 = Follow.objects.values_list('author').filter(user=user1)
        post_list1 = Post.objects.filter(author__in=authors1)
        post1 = Post.objects.create(author=author,
                                    text='Тестовый текст',)
        self.assertIn(post1, post_list1)
        authors2 = Follow.objects.values_list('author').filter(user=user2)
        post_list2 = Post.objects.filter(author__in=authors2)
        self.assertNotIn(post1, post_list2)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        object_list = []
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый текст',
                group=cls.group,
            )
            object_list.append(cls.post)

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_index_group_list_profile_page_contains_ten_records(self):
        """Проверка паджинатора первой страницы index, group_list, profile."""
        paginator_responses = [
            self.client.get(reverse('posts:index')),
            self.client.get(reverse('posts:group_list',
                                    kwargs={'slug': 'test-slug'})),
            self.client.get(reverse('posts:profile',
                                    kwargs={'username': 'auth'})),
        ]
        for response in paginator_responses:
            self.assertEqual(len(response.context['page_obj']),
                             settings.ARTICLES_SELECTION)

    def test_second_index_group_list_profile_page_contains_three_records(self):
        """Проверка паджинатора второй страницы index, group_list, profile."""
        paginator_responses = [
            self.client.get(reverse('posts:index') + '?page=2'),
            self.client.get(reverse('posts:group_list',
                                    kwargs={'slug': 'test-slug'}) + '?page=2'),
            self.client.get(reverse('posts:profile',
                                    kwargs={'username': 'auth'}) + '?page=2'),
        ]
        for response in paginator_responses:
            self.assertEqual(len(response.context['page_obj']), 3)
