from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Avg, F
from games.models import Game, Genre
from games.steam import get_steam_game_details
from reviews.models import Review
from reviews.forms import ReviewForm


@method_decorator(never_cache, name='get')
class GameListView(View):
    template_name = 'games/game_list.html'

    def get(self, request):
        games = Game.objects.annotate(avg_rating=Avg('review__rating'))
        genres = Genre.objects.all().order_by('name')

        genre_slug = request.GET.get('genre')
        if genre_slug:
            games = games.filter(gamegenre__genre__slug=genre_slug)

        query = request.GET.get('q')
        if query:
            games = games.filter(title__icontains=query)

        sort = request.GET.get('sort')
        if sort == 'rating':
            games = games.order_by(F('avg_rating').desc(nulls_last=True))
        else:
            games = games.order_by('title')

        paginator = Paginator(games, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        num_pages = paginator.num_pages
        first_pages = list(range(1, min(4, num_pages + 1)))
        last_pages = list(range(max(num_pages - 2, 4), num_pages + 1))
        show_dots = last_pages and last_pages[0] > first_pages[-1] + 1

        games_version = cache.get('games_list_version', 0)

        return render(request, self.template_name, {
            'page_obj': page_obj,
            'genres': genres,
            'selected_genre': genre_slug,
            'query': query or '',
            'sort': sort or '',
            'first_pages': first_pages,
            'last_pages': last_pages,
            'show_dots': show_dots,
            'games_version': games_version,
        })


class GameDeleteView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.groups.filter(name='Moderator').exists():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, slug):
        game = get_object_or_404(Game, slug=slug)
        return render(request, 'games/game_confirm_delete.html', {'game': game})

    def post(self, request, slug):
        game = get_object_or_404(Game, slug=slug)
        game.delete()
        return redirect('games')


class GameDetailView(View):
    template_name = 'games/game_detail.html'

    def get(self, request, slug):
        game = get_object_or_404(Game, slug=slug)
        genres = game.gamegenre_set.select_related('genre').all()

        steam_data = None
        if game.steam_app_id:
            steam_data = get_steam_game_details(game.steam_app_id)

        user_review = None
        review_form = None
        if request.user.is_authenticated:
            user_review = Review.objects.filter(author=request.user, game=game).first()
            if not user_review:
                review_form = ReviewForm()

        reviews = Review.objects.filter(game=game).select_related('author').order_by('-created_at')
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']

        rating_filter = request.GET.get('rating', '').strip()
        if rating_filter.isdigit() and 1 <= int(rating_filter) <= 10:
            reviews = reviews.filter(rating=int(rating_filter))

        return render(request, self.template_name, {
            'game': game,
            'genres': genres,
            'steam_data': steam_data,
            'review_form': review_form,
            'user_review': user_review,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'rating_filter': rating_filter,
            'rating_choices': range(10, 0, -1),
        })