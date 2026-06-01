import requests
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from games.models import Game, Genre, GameGenre
from games.steam import search_steam_app_id


class Command(BaseCommand):
    help = 'Заполняет базу данных играми из RAWG API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Количество страниц для загрузки (20 игр на страницу)'
        )

    def handle(self, *args, **options):
        api_key = settings.RAWG_API_KEY
        pages = options['pages']
        base_url = 'https://api.rawg.io/api'

        self.stdout.write('Загружаем жанры...')
        self.load_genres(base_url, api_key)

        self.stdout.write('Загружаем игры...')
        self.load_games(base_url, api_key, pages)

        self.stdout.write(self.style.SUCCESS('Готово!'))

    def load_genres(self, base_url, api_key):
        url = f'{base_url}/genres'
        response = requests.get(url, params={'key': api_key})
        data = response.json()

        for item in data.get('results', []):
            genre, created = Genre.objects.get_or_create(
                slug=item['slug'],
                defaults={'name': item['name']}
            )
            if created:
                self.stdout.write(f'  Жанр: {genre.name}')

    def load_games(self, base_url, api_key, pages):
        for page in range(1, pages + 1):
            self.stdout.write(f'  Страница {page}/{pages}...')
            url = f'{base_url}/games'
            response = requests.get(url, params={
                'key': api_key,
                'page': page,
                'page_size': 20,
                'ordering': '-rating',
            })
            data = response.json()

            for item in data.get('results', []):
                self.save_game(item)

            time.sleep(0.5)

    def save_game(self, item):
        detail_url = f'https://api.rawg.io/api/games/{item["slug"]}'
        detail_response = requests.get(detail_url, params={'key': settings.RAWG_API_KEY})
        detail = detail_response.json()

        developer = None
        if detail.get('developers'):
            developer = detail['developers'][0]['name']

        description = detail.get('description_raw', '') or ''

        game, created = Game.objects.get_or_create(
            slug=item['slug'],
            defaults={
                'title': item['name'],
                'description': description,
                'cover': item.get('background_image', ''),
                'release_date': item.get('released'),
                'developer': developer,
            }
        )

        if created:
            # Привязываем жанры
            for genre_data in item.get('genres', []):
                try:
                    genre = Genre.objects.get(slug=genre_data['slug'])
                    GameGenre.objects.get_or_create(game=game, genre=genre)
                except Genre.DoesNotExist:
                    pass

            # Ищем Steam App ID
            steam_app_id = search_steam_app_id(item['name'])
            if steam_app_id:
                game.steam_app_id = steam_app_id
                game.save()
                self.stdout.write(f'    + {game.title} (Steam ID: {steam_app_id})')
            else:
                self.stdout.write(f'    + {game.title} (Steam ID не найден)')

        time.sleep(0.3)