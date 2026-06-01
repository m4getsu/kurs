from django.urls import path
from social import views

urlpatterns = [
    path('social/like/status/', views.LikeStatusView.as_view(), name='like_status'),
    path('social/like/', views.LikeView.as_view(), name='like'),
    path('social/follow/<str:username>/', views.FollowView.as_view(), name='follow'),
]
