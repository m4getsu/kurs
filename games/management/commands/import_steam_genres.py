import time
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from games.models import Game, Genre, GameGenre
from games.steam import get_steam_game_details


class Command(BaseCommand):
    help = 'Подтягивает жанры к играм в БД через Steam API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only-empty',
            action='store_true',
            default=True,
            help='Обрабатывать только игры без жанров (по умолчанию включено)',
        )

    def handle(self, *args, **options):
        games = Game.objects.filter(steam_app_id__isnull=False)
        if options['only_empty']:
            games = games.exclude(gamegenre__isnull=False)

        total = games.count()
        self.stdout.write(f'Игр для обработки: {total}')

        updated = 0
        skipped = 0

        for i, game in enumerate(games, 1):
            self.stdout.write(f'[{i}/{total}] {game.title}...', ending=' ')

            details = get_steam_game_details(game.steam_app_id)
            if not details or not details.get('genres'):
                self.stdout.write('нет данных')
                skipped += 1
                time.sleep(0.5)
                continue

            added = []
            for genre_name in details['genres']:
                slug = slugify(genre_name) or f'genre-{genre_name}'
                genre, _ = Genre.objects.get_or_create(
                    slug=slug,
                    defaults={'name': genre_name},
                )
                GameGenre.objects.get_or_create(game=game, genre=genre)
                added.append(genre_name)

            self.stdout.write(f'{", ".join(added)}')
            updated += 1
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово. Обновлено: {updated}, пропущено: {skipped}'
        ))
