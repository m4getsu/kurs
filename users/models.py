from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from PIL import Image

AVATAR_SIZE = (200, 200)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    steam_id = models.CharField(max_length=100, blank=True, null=True)
    is_banned = models.BooleanField(default=False)
    banned_until = models.DateTimeField(blank=True, null=True)
    ban_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'profile'

    def __str__(self):
        return f'Профиль {self.user.username}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.size != AVATAR_SIZE:
                img = img.resize(AVATAR_SIZE, Image.LANCZOS)
                img.save(self.avatar.path)
            img.close()


class User(AbstractUser):
    email = models.EmailField(unique=True)

    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.username


class UserGameList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey('games.Game', on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    hours_played = models.DecimalField(max_digits=8, decimal_places=2)
    added_at = models.DateTimeField()

    class Meta:
        db_table = 'user_game_list'
        unique_together = (('user', 'game'),)