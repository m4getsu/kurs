from django.db import models
from django.conf import settings

class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='follow_following_set')
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'follow'
        unique_together = (('follower', 'following'),)


class Like(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, blank=True, null=True)
    review = models.ForeignKey('reviews.Review', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'like'
        unique_together = (('user', 'post'), ('user', 'review'),)
