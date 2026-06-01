from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from reviews.models import Review


@receiver([post_save, post_delete], sender=Review)
def invalidate_games_list_cache(sender, **kwargs):
    cache.set('games_list_version', cache.get('games_list_version', 0) + 1)
