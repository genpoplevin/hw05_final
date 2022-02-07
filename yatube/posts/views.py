from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.select_related('group')
    paginator = Paginator(post_list, settings.ARTICLES_SELECTION)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, settings.ARTICLES_SELECTION)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = author.following.exists()
    post_list = author.posts.all().order_by('author')
    paginator = Paginator(post_list, settings.ARTICLES_SELECTION)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_number = post_list.count()
    context = {
        'page_obj': page_obj,
        'post_number': post_number,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_list = Post.objects.select_related(
        'group'
    ).filter(
        author_id=post.author
    )
    post_number = post_list.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'form': form,
        'comments': comments,
        'post': post,
        'post_list': post_list,
        'post_number': post_number,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    context = {
        'form': form,
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(f'/profile/{post.author.username}/')
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    context = {
        'form': form,
        'post_id': post_id,
        'post': post,
        'is_edit': True,
    }
    if request.user == post.author and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(f'/posts/{post.id}', id=post_id)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Получаем пост
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Выводит посты авторов, на которых
       подписан текущий пользователь."""
    # Информация о текущем пользователе доступна в переменной request.user
    user = request.user
    post_list = Post.objects.values('author').filter(
        author__following__user=user)
    paginator = Paginator(post_list, settings.ARTICLES_SELECTION)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Делает подписку на автора."""
    # Подписаться на автора
    user = request.user
    author = get_object_or_404(User, username=username)
    if author != user:
        user.follower.get_or_create(user=user,
                                    author=author)

    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписывает пользователя от автора."""
    # отписка
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=user,
                                   author=author)
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username)
