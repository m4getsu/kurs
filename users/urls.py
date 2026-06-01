from django.urls import path
from users import views

urlpatterns = [
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    path('accounts/logout/', views.LogoutView.as_view(), name='logout'),
    path('accounts/verify-email/<uidb64>/<token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('banned/', views.BannedView.as_view(), name='banned'),
]