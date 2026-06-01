from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import get_user_model
from social.models import Like, Follow
from posts.models import Post
from reviews.models import Review

User = get_user_model()


class LikeStatusView(View):

    def get(self, request):
        post_id = request.GET.get('post_id')
        review_id = request.GET.get('review_id')

        if post_id:
            try:
                post = Post.objects.get(pk=post_id)
            except Post.DoesNotExist:
                return JsonResponse({'error': 'Пост не найден'}, status=404)
            liked = (
                request.user.is_authenticated and
                Like.objects.filter(user=request.user, post=post, review=None).exists()
            )
            count = Like.objects.filter(post=post, review=None).count()

        elif review_id:
            try:
                review = Review.objects.get(pk=review_id)
            except Review.DoesNotExist:
                return JsonResponse({'error': 'Рецензия не найдена'}, status=404)
            liked = (
                request.user.is_authenticated and
                Like.objects.filter(user=request.user, review=review, post=None).exists()
            )
            count = Like.objects.filter(review=review, post=None).count()

        else:
            return JsonResponse({'error': 'Необходимо передать post_id или review_id'}, status=400)

        return JsonResponse({'liked': liked, 'count': count})


@method_decorator(require_POST, name='dispatch')
class LikeView(View):

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        post_id = request.POST.get('post_id')
        review_id = request.POST.get('review_id')

        if post_id and review_id:
            return JsonResponse({'error': 'Укажите либо post_id, либо review_id'}, status=400)

        if post_id:
            try:
                post = Post.objects.get(pk=post_id)
            except Post.DoesNotExist:
                return JsonResponse({'error': 'Пост не найден'}, status=404)
            like = Like.objects.filter(user=request.user, post=post, review=None).first()
            if like:
                like.delete()
                liked = False
            else:
                Like.objects.create(user=request.user, post=post, review=None, created_at=timezone.now())
                liked = True
            count = Like.objects.filter(post=post, review=None).count()

        elif review_id:
            try:
                review = Review.objects.get(pk=review_id)
            except Review.DoesNotExist:
                return JsonResponse({'error': 'Рецензия не найдена'}, status=404)
            like = Like.objects.filter(user=request.user, review=review, post=None).first()
            if like:
                like.delete()
                liked = False
            else:
                Like.objects.create(user=request.user, review=review, post=None, created_at=timezone.now())
                liked = True
            count = Like.objects.filter(review=review, post=None).count()

        else:
            return JsonResponse({'error': 'Необходимо передать post_id или review_id'}, status=400)

        return JsonResponse({'liked': liked, 'count': count})


@method_decorator(require_POST, name='dispatch')
class FollowView(View):

    def post(self, request, username):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        target = get_object_or_404(User, username=username)

        if target == request.user:
            return JsonResponse({'error': 'Нельзя подписаться на себя'}, status=400)

        follow = Follow.objects.filter(follower=request.user, following=target).first()
        if follow:
            follow.delete()
            following = False
        else:
            Follow.objects.create(follower=request.user, following=target, created_at=timezone.now())
            following = True

        count = Follow.objects.filter(following=target).count()
        return JsonResponse({'following': following, 'count': count})
