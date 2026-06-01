from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.views import View
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from posts.models import Post, Comment, PostImage
from posts.forms import PostForm, CommentForm
from social.models import Like, Follow


class PostListView(View):
    template_name = 'posts/post_list.html'
    paginate_by = 10

    def get(self, request):
        tag = request.GET.get('tag', '').strip()
        if request.user.is_authenticated:
            posts = Post.objects.filter(
                Q(is_published=True) | Q(author=request.user)
            ).distinct().order_by('-created_at')
        else:
            posts = Post.objects.filter(is_published=True).order_by('-created_at')
        if tag:
            posts = posts.filter(tags__icontains=tag)
        paginator = Paginator(posts, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        from collections import Counter
        from django.contrib.auth import get_user_model
        from games.models import Game
        User = get_user_model()

        all_tags = Post.objects.filter(is_published=True).exclude(tags='').exclude(tags__isnull=True).values_list('tags', flat=True)
        tag_counter = Counter()
        for tag_str in all_tags:
            for t in tag_str.replace(',', ' ').split():
                t = t.strip()
                if t:
                    tag_counter[t] += 1
        popular_tags = tag_counter.most_common(12)

        week_ago = timezone.now() - timedelta(days=7)
        top_author_ids = (
            Post.objects.filter(is_published=True, created_at__gte=week_ago)
            .values('author_id')
            .annotate(post_count=Count('id'))
            .order_by('-post_count')[:4]
        )
        author_id_map = {row['author_id']: row['post_count'] for row in top_author_ids}
        active_authors = User.objects.filter(pk__in=author_id_map.keys()).select_related('profile')
        for author in active_authors:
            author.recent_post_count = author_id_map[author.pk]
            author.is_followed = (
                request.user.is_authenticated and
                Follow.objects.filter(follower=request.user, following=author).exists()
            )

        recommended_games = Game.objects.filter(cover__isnull=False).exclude(cover='').order_by('?')[:4]

        return render(request, self.template_name, {
            'page_obj': page_obj,
            'current_tag': tag,
            'popular_tags': popular_tags,
            'active_authors': active_authors,
            'recommended_games': recommended_games,
        })


class PostDetailView(View):
    template_name = 'posts/post_detail.html'

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        is_moderator = request.user.is_authenticated and request.user.groups.filter(name='Moderator').exists()
        is_author = request.user.is_authenticated and post.author == request.user
        if not post.is_published and not is_moderator and not is_author:
            raise Http404
        comments = post.comment_set.select_related('author').order_by('created_at')
        form = CommentForm()
        can_edit = is_author or is_moderator
        likes_count = Like.objects.filter(post=post, review=None).count()
        user_liked = (
            request.user.is_authenticated and
            Like.objects.filter(user=request.user, post=post, review=None).exists()
        )
        return render(request, self.template_name, {
            'post': post,
            'comments': comments,
            'form': form,
            'can_edit': can_edit,
            'likes_count': likes_count,
            'user_liked': user_liked,
            'is_moderator': is_moderator,
        })

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        is_moderator = request.user.is_authenticated and request.user.groups.filter(name='Moderator').exists()
        is_author = request.user.is_authenticated and post.author == request.user
        if not post.is_published and not is_moderator and not is_author:
            raise Http404
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.created_at = timezone.now()
            comment.save()
            return redirect('post_detail', pk=pk)
        comments = post.comment_set.select_related('author').order_by('created_at')
        return render(request, self.template_name, {
            'post': post,
            'comments': comments,
            'form': form,
        })


class PostCreateView(LoginRequiredMixin, View):
    template_name = 'posts/post_create.html'
    login_url = '/accounts/login/'

    def get(self, request):
        form = PostForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.created_at = timezone.now()
            post.updated_at = timezone.now()
            post.save()
            for i, f in enumerate(request.FILES.getlist('images')):
                PostImage.objects.create(post=post, image=f, order=i)
            return redirect('post_detail', pk=post.pk)
        return render(request, self.template_name, {'form': form})


class PostEditView(LoginRequiredMixin, View):
    template_name = 'posts/post_edit.html'
    login_url = '/accounts/login/'

    def _get_post_or_403(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        is_moderator = request.user.groups.filter(name='Moderator').exists()
        if post.author != request.user and not is_moderator:
            raise PermissionDenied
        return post

    def get(self, request, pk):
        post = self._get_post_or_403(request, pk)
        form = PostForm(instance=post)
        return render(request, self.template_name, {'form': form, 'post': post})

    def post(self, request, pk):
        post = self._get_post_or_403(request, pk)
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            edited_post = form.save(commit=False)
            edited_post.updated_at = timezone.now()
            edited_post.save()
            existing_count = post.images.count()
            for i, f in enumerate(request.FILES.getlist('images')):
                PostImage.objects.create(post=post, image=f, order=existing_count + i)
            return redirect('post_detail', pk=post.pk)
        return render(request, self.template_name, {'form': form, 'post': post})


class PostDeleteView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def _get_post_or_403(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        is_moderator = request.user.groups.filter(name='Moderator').exists()
        if post.author != request.user and not is_moderator:
            raise PermissionDenied
        return post

    def get(self, request, pk):
        post = self._get_post_or_403(request, pk)
        return render(request, 'posts/post_confirm_delete.html', {'post': post})

    def post(self, request, pk):
        post = self._get_post_or_403(request, pk)
        post.delete()
        return redirect('post_list')


class PostImageDeleteView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        img = get_object_or_404(PostImage, pk=pk)
        is_moderator = request.user.groups.filter(name='Moderator').exists()
        if img.post.author != request.user and not is_moderator:
            raise PermissionDenied
        post_pk = img.post.pk
        img.image.delete(save=False)
        img.delete()
        return redirect('post_edit', pk=post_pk)


class CommentDeleteView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        is_moderator = request.user.groups.filter(name='Moderator').exists()
        if comment.author != request.user and not is_moderator:
            raise PermissionDenied
        post_pk = comment.post.pk
        comment.delete()
        return redirect('post_detail', pk=post_pk)


class FeedView(View):
    template_name = 'posts/feed.html'
    paginate_by = 12

    def get(self, request):
        from reviews.models import Review
        if request.user.is_authenticated:
            followed_ids = list(Follow.objects.filter(
                follower=request.user
            ).values_list('following_id', flat=True))
            if followed_ids:
                posts = list(Post.objects.filter(
                    author_id__in=followed_ids, is_published=True
                ).select_related('author'))
                reviews = list(Review.objects.filter(
                    author_id__in=followed_ids
                ).select_related('author', 'game'))
            else:
                posts = list(Post.objects.filter(is_published=True).select_related('author'))
                reviews = list(Review.objects.all().select_related('author', 'game'))
        else:
            posts = list(Post.objects.filter(is_published=True).select_related('author'))
            reviews = list(Review.objects.all().select_related('author', 'game'))

        for item in posts:
            item.item_type = 'post'
        for item in reviews:
            item.item_type = 'review'

        feed_items = sorted(posts + reviews, key=lambda x: x.created_at, reverse=True)

        paginator = Paginator(feed_items, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.GET.get('partial'):
            from django.template.loader import render_to_string
            from django.http import JsonResponse
            html = render_to_string('posts/feed_items.html', {'page_obj': page_obj}, request=request)
            return JsonResponse({
                'html': html,
                'has_next': page_obj.has_next(),
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            })

        from games.models import Game
        from django.contrib.auth import get_user_model
        User = get_user_model()

        recommended_games = Game.objects.filter(cover__isnull=False).exclude(cover='').order_by('?')[:4]

        week_ago = timezone.now() - timedelta(days=7)
        top_author_ids = (
            Post.objects.filter(is_published=True, created_at__gte=week_ago)
            .values('author_id')
            .annotate(post_count=Count('id'))
            .order_by('-post_count')[:3]
        )
        author_id_map = {row['author_id']: row['post_count'] for row in top_author_ids}
        active_authors = User.objects.filter(pk__in=author_id_map.keys()).select_related('profile')
        for author in active_authors:
            author.recent_post_count = author_id_map[author.pk]
            author.is_followed = (
                request.user.is_authenticated and
                Follow.objects.filter(follower=request.user, following=author).exists()
            )

        return render(request, self.template_name, {
            'page_obj': page_obj,
            'recommended_games': recommended_games,
            'active_authors': active_authors,
        })


class SearchView(View):
    template_name = 'posts/search.html'

    def get(self, request):
        from games.models import Game
        from users.models import User
        q = request.GET.get('q', '').strip()
        from urllib.parse import quote, unquote
        last_query = unquote(request.COOKIES.get('last_search', ''))
        games, posts, users = [], [], []
        search_term = q or last_query
        if search_term:
            games = Game.objects.filter(title__icontains=search_term).order_by('title')[:10]
            posts = Post.objects.filter(
                Q(title__icontains=search_term) | Q(content__icontains=search_term) | Q(tags__icontains=search_term),
                is_published=True
            ).select_related('author').order_by('-created_at')[:10]
            users = User.objects.filter(username__icontains=search_term).order_by('username')[:10]
        response = render(request, self.template_name, {
            'q': search_term,
            'games': games,
            'posts': posts,
            'users': users,
            'from_cookie': bool(last_query and not q),
        })
        if q:
            response.set_cookie('last_search', quote(q), max_age=30 * 24 * 60 * 60)
        return response
