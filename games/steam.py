import requests


def search_steam_app_id(title):
    """Ищет игру в Steam по названию, возвращает app_id или None."""
    try:
        url = 'https://store.steampowered.com/api/storesearch/'
        response = requests.get(url, params={
            'term': title,
            'l': 'english',
            'cc': 'US',
        }, timeout=5)
        data = response.json()
        items = data.get('items', [])
        if items:
            return items[0]['id']
        return None
    except Exception:
        return None


def get_steam_game_details(app_id):
    """Получает детальную информацию об игре из Steam Store."""
    try:
        url = f'https://store.steampowered.com/api/appdetails'
        response = requests.get(url, params={
            'appids': app_id,
            'l': 'english',
        }, timeout=5)
        data = response.json()
        game_data = data.get(str(app_id), {})

        if not game_data.get('success'):
            return None

        details = game_data['data']

        screenshots = [
            s['path_full'] for s in details.get('screenshots', [])[:6]
        ]

        metacritic = details.get('metacritic', {})

        return {
            'steam_url': f'https://store.steampowered.com/app/{app_id}/',
            'short_description': details.get('short_description', ''),
            'screenshots': screenshots,
            'metacritic_score': metacritic.get('score'),
            'metacritic_url': metacritic.get('url'),
            'recommendations': details.get('recommendations', {}).get('total'),
            'header_image': details.get('header_image', ''),
            'developers': details.get('developers', []),
            'publishers': details.get('publishers', []),
            'genres': [g['description'] for g in details.get('genres', [])],
        }
    except Exception:
        return None