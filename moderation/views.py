import urllib.parse
from collections import defaultdict
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.utils import timezone
from django.views import View
from users.mixins import ModeratorRequiredMixin
from users.models import User
from posts.models import Post
from reviews.models import Review
from moderation.models import Report
from moderation.forms import ReportForm, BanForm

PAGE_SIZE = 20


class ModerationView(ModeratorRequiredMixin, View):
    template_name = 'moderation/moderation.html'

    def get(self, request):
        q_posts = request.GET.get('q_posts', '').strip()
        published = request.GET.get('published', '')
        sort_posts = request.GET.get('sort_posts', '')

        q_reviews = request.GET.get('q_reviews', '').strip()
        sort_reviews = request.GET.get('sort_reviews', '')

        q_users = request.GET.get('q_users', '').strip()
        status = request.GET.get('status', '')
        sort_users = request.GET.get('sort_users', '')

        post_ct = ContentType.objects.get_for_model(Post)
        review_ct = ContentType.objects.get_for_model(Review)
        user_ct = ContentType.objects.get_for_model(User)

        open_reports = Report.objects.filter(is_resolved=False).select_related('user')
        reports_map = defaultdict(list)
        for report in open_reports:
            reports_map[(report.content_type_id, report.object_id)].append(report)

        posts_qs = Post.objects.select_related('author').order_by('-created_at')
        if q_posts:
            posts_qs = posts_qs.filter(title__icontains=q_posts)
        if published == 'yes':
            posts_qs = posts_qs.filter(is_published=True)
        elif published == 'no':
            posts_qs = posts_qs.filter(is_published=False)
        all_posts = list(posts_qs)
        for post in all_posts:
            post.open_reports = reports_map.get((post_ct.id, post.pk), [])
        if sort_posts == 'reports':
            all_posts.sort(key=lambda p: len(p.open_reports), reverse=True)
        posts_page = Paginator(all_posts, PAGE_SIZE).get_page(request.GET.get('posts_page'))

        reviews_qs = Review.objects.select_related('author', 'game').order_by('-created_at')
        if q_reviews:
            reviews_qs = reviews_qs.filter(
                Q(game__title__icontains=q_reviews) | Q(author__username__icontains=q_reviews)
            )
        all_reviews = list(reviews_qs)
        for review in all_reviews:
            review.open_reports = reports_map.get((review_ct.id, review.pk), [])
        if sort_reviews == 'reports':
            all_reviews.sort(key=lambda r: len(r.open_reports), reverse=True)
        reviews_page = Paginator(all_reviews, PAGE_SIZE).get_page(request.GET.get('reviews_page'))

        users_qs = User.objects.select_related('profile').order_by('-date_joined')
        if q_users:
            users_qs = users_qs.filter(
                Q(username__icontains=q_users) | Q(email__icontains=q_users)
            )
        if status == 'active':
            users_qs = users_qs.filter(profile__is_banned=False)
        elif status == 'banned':
            users_qs = users_qs.filter(profile__is_banned=True)
        all_users = list(users_qs)
        for user in all_users:
            user.open_reports = reports_map.get((user_ct.id, user.pk), [])
        if sort_users == 'reports':
            all_users.sort(key=lambda u: len(u.open_reports), reverse=True)
        users_page = Paginator(all_users, PAGE_SIZE).get_page(request.GET.get('users_page'))

        page_params = {k: v for k, v in request.GET.items() if k not in ('posts_page', 'reviews_page', 'users_page')}
        base_query = (urllib.parse.urlencode(page_params) + '&') if page_params else ''

        return render(request, self.template_name, {
            'posts': posts_page,
            'reviews': reviews_page,
            'users': users_page,
            'base_query': base_query,
            'q_posts': q_posts, 'published': published, 'sort_posts': sort_posts,
            'q_reviews': q_reviews, 'sort_reviews': sort_reviews,
            'q_users': q_users, 'status': status, 'sort_users': sort_users,
        })


class ReportCreateView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, app_label, model_name, object_id):
        content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)

        if Report.objects.filter(user=request.user, content_type=content_type, object_id=object_id).exists():
            return redirect(request.META.get('HTTP_REFERER', '/'))

        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.content_type = content_type
            report.object_id = object_id
            report.created_at = timezone.now()
            report.save()

        return redirect(request.META.get('HTTP_REFERER', '/'))


class ReportResolveView(ModeratorRequiredMixin, View):

    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        report.is_resolved = True
        report.save()
        return redirect('moderation')


class BanUserView(ModeratorRequiredMixin, View):
    template_name = 'moderation/ban_user.html'

    def get(self, request, username):
        target = get_object_or_404(User, username=username)
        form = BanForm()
        return render(request, self.template_name, {'form': form, 'target': target})

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        form = BanForm(request.POST)
        if form.is_valid():
            profile = target.profile
            profile.is_banned = True
            profile.banned_until = form.cleaned_data['banned_until']
            profile.ban_reason = form.cleaned_data['reason']
            profile.save()
            return redirect('moderation')
        return render(request, self.template_name, {'form': form, 'target': target})


class UnbanUserView(ModeratorRequiredMixin, View):

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        profile = target.profile
        profile.is_banned = False
        profile.banned_until = None
        profile.ban_reason = None
        profile.save()
        return redirect('moderation')
