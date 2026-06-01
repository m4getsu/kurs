from django.urls import path
from moderation import views

urlpatterns = [
    path('moderation/', views.ModerationView.as_view(), name='moderation'),
    path('moderation/report/<str:app_label>/<str:model_name>/<int:object_id>/', views.ReportCreateView.as_view(), name='report_create'),
    path('moderation/report/<int:pk>/resolve/', views.ReportResolveView.as_view(), name='report_resolve'),
    path('moderation/ban/<str:username>/', views.BanUserView.as_view(), name='ban_user'),
    path('moderation/unban/<str:username>/', views.UnbanUserView.as_view(), name='unban_user'),
]
