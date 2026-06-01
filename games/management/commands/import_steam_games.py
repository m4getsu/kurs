import time
import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from games.models import Game
from games.steam import get_steam_game_details

STEAMSPY_ENDPOINTS = [
    'top100in2weeks',
    'top100forever',
    'top100owned',
]


def get_steamspy_top(request_type):
    try:
        response = requests.get(
            'https://steamspy.com/api.php',
            params={'request': request_type},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {}


class Command(BaseCommand):
    help = 'Импортирует популярные игры из SteamSpy (top100in2weeks, top100forever, top100owned)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=1,
            help='Количество списков для загрузки: 1=top100in2weeks, 2=+top100forever, 3=+top100owned',
        )
        parser.add_argument(
            '--no-details',
            action='store_true',
            help='Не запрашивать детали из Steam API (быстрее, но без описания и даты выхода)',
        )

    def handle(self, *args, **options):
        pages = min(options['pages'], len(STEAMSPY_ENDPOINTS))
        fetch_details = not options['no_details']
        total_created = 0
        total_skipped = 0

        for i in range(pages):
            endpoint = STEAMSPY_ENDPOINTS[i]
            self.stdout.write(f'\nЗагружаем {endpoint} из SteamSpy...')

            data = get_steamspy_top(endpoint)
            if not data:
                self.stderr.write(f'Не удалось получить данные для {endpoint}')
                continue

            for app_id_str, game_data in data.items():
                try:
                    app_id = int(app_id_str)
                    name = (game_data.get('name') or '').strip()
                    if not name:
                        continue

                    if Game.objects.filter(steam_app_id=app_id).exists():
                        total_skipped += 1
                        continue

                    base_slug = slugify(name) or f'game-{app_id}'
                    slug = base_slug
                    counter = 1
                    while Game.objects.filter(slug=slug).exists():
                        slug = f'{base_slug}-{counter}'
                        counter += 1

                    cover = f'https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg'
                    description = None
                    release_date = None
                    developer = game_data.get('developer') or None

                    if fetch_details:
                        details = get_steam_game_details(app_id)
                        if details:
                            description = details.get('short_description') or None
                            developer = (details.get('developers') or [None])[0] or developer
                        time.sleep(0.5)

                    Game.objects.create(
                        title=name,
                        slug=slug,
                        description=description,
                        cover=cover,
                        release_date=release_date,
                        developer=developer,
                        steam_app_id=app_id,
                    )
                    total_created += 1
                    self.stdout.write(f'  + {name} (appid: {app_id})')

                except Exception as e:
                    self.stderr.write(f'Ошибка при сохранении {app_id_str}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово. Добавлено: {total_created}, пропущено (уже есть): {total_skipped}'
        ))
