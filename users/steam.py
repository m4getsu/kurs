import re
import requests
from django.conf import settings


def resolve_steam_id(steam_input):
    """
    Принимает любой формат — числовой ID или ссылку на профиль.
    Возвращает числовой Steam ID (строка) или None если не удалось.
    """
    if not steam_input:
        return None

    steam_input = steam_input.strip()

    if re.match(r'^\d{17}$', steam_input):
        return steam_input

    match = re.search(r'/profiles/(\d{17})', steam_input)
    if match:
        return match.group(1)

    match = re.search(r'/id/([^/]+)', steam_input)
    if match:
        username = match.group(1)
        return resolve_vanity_url(username)

    return resolve_vanity_url(steam_input)


def resolve_vanity_url(username):
    try:
        url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
        response = requests.get(url, params={
            'key': settings.STEAM_API_KEY,
            'vanityurl': username,
        }, timeout=5)
        data = response.json()
        if data.get('response', {}).get('success') == 1:
            return data['response']['steamid']
        return None
    except Exception:
        return None


def get_steam_games(steam_id):
    try:
        url = 'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/'
        response = requests.get(url, params={
            'key': settings.STEAM_API_KEY,
            'steamid': steam_id,
            'include_appinfo': True,
            'include_played_free_games': True,
        }, timeout=5)
        data = response.json()
        games = data.get('response', {}).get('games', [])
        games.sort(key=lambda x: x.get('playtime_forever', 0), reverse=True)

        result = []
        for game in games[:20]:
            playtime = game.get('playtime_forever', 0)
            result.append({
                'name': game.get('name', ''),
                'appid': game.get('appid'),
                'playtime_hours': round(playtime / 60, 1),
                'icon_url': f"https://media.steampowered.com/steamcommunity/public/images/apps/{game['appid']}/{game.get('img_icon_url', '')}.jpg" if game.get(
                    'img_icon_url') else None,
            })
        return result

    except Exception:
        return []