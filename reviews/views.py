from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views import View
from games.models import Game
from reviews.models import Review
from reviews.forms import ReviewForm


class ReviewCreateView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, slug):
        game = get_object_or_404(Game, slug=slug)

        if Review.objects.filter(author=request.user, game=game).exists():
            return redirect('game_detail', slug=slug)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.author = request.user
            review.game = game
            review.created_at = timezone.now()
            review.updated_at = timezone.now()
            review.save()

        return redirect('game_detail', slug=slug)


class ReviewEditView(LoginRequiredMixin, View):
    template_name = 'reviews/review_edit.html'
    login_url = '/accounts/login/'

    def _get_review_or_403(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if review.author != request.user:
            raise PermissionDenied
        return review

    def get(self, request, pk):
        review = self._get_review_or_403(request, pk)
        form = ReviewForm(instance=review)
        return render(request, self.template_name, {'form': form, 'review': review})

    def post(self, request, pk):
        review = self._get_review_or_403(request, pk)
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            edited = form.save(commit=False)
            edited.updated_at = timezone.now()
            edited.save()
            return redirect('game_detail', slug=review.game.slug)
        return render(request, self.template_name, {'form': form, 'review': review})


class ReviewDeleteView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def _get_review_or_403(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        is_moderator = request.user.groups.filter(name='Moderator').exists()
        if review.author != request.user and not is_moderator:
            raise PermissionDenied
        return review

    def get(self, request, pk):
        review = self._get_review_or_403(request, pk)
        return render(request, 'reviews/review_confirm_delete.html', {'review': review})

    def post(self, request, pk):
        review = self._get_review_or_403(request, pk)
        slug = review.game.slug
        review.delete()
        return redirect('game_detail', slug=slug)
