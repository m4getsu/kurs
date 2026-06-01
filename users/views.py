from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from users.forms import RegisterForm, ProfileEditForm
from users.models import User, Profile
from posts.models import Post
from social.models import Follow
from reviews.models import Review
from users.steam import resolve_steam_id, get_steam_games



class RegisterView(View):
    template_name = 'users/register.html'

    def get(self, request):
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verify_url = request.build_absolute_uri(
                f'/accounts/verify-email/{uid}/{token}/'
            )
            send_mail(
                subject='Email verification - Igrovorot',
                message=f'Click to verify your email: {verify_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
            messages.success(request, 'На почту отправлено письмо для подтверждения.')
            return redirect('login')
        return render(request, self.template_name, {'form': form})


class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            messages.success(request, 'Email подтверждён, добро пожаловать!')
            return redirect('home')
        else:
            messages.error(request, 'Ссылка недействительна или устарела.')
            return redirect('login')

class LoginView(View):
    template_name = 'users/login.html'

    def get(self, request):
        form = AuthenticationForm(request)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        messages.error(request, 'Неверный email или пароль.')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')

class BannedView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            profile = request.user.profile
            if not profile.is_banned:
                return redirect('feed')
        except Exception:
            return redirect('login')
        return render(request, 'users/banned.html', {'profile': profile})


class ProfileView(View):
    template_name = 'users/profile.html'

    def get(self, request, username):
        profile_user = get_object_or_404(User, username=username)
        profile, _ = Profile.objects.get_or_create(user=profile_user)
        if request.user == profile_user:
            posts = Post.objects.filter(author=profile_user).order_by('-created_at')
        else:
            posts = Post.objects.filter(author=profile_user, is_published=True).order_by('-created_at')
        reviews = Review.objects.filter(author=profile_user).select_related('game').order_by('-created_at')
        followers_count = Follow.objects.filter(following=profile_user).count()
        following_count = Follow.objects.filter(follower=profile_user).count()
        is_following = (
            request.user.is_authenticated and
            Follow.objects.filter(follower=request.user, following=profile_user).exists()
        )
        steam_games = []
        if profile.steam_id:
            steam_id = resolve_steam_id(profile.steam_id)
            if steam_id:
                steam_games = get_steam_games(steam_id)
        return render(request, self.template_name, {
            'profile_user': profile_user,
            'profile': profile,
            'posts': posts,
            'reviews': reviews,
            'followers_count': followers_count,
            'following_count': following_count,
            'is_following': is_following,
            'steam_games': steam_games,
        })


class ProfileEditView(LoginRequiredMixin, View):
    template_name = 'users/profile_edit.html'
    login_url = '/accounts/login/'

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = ProfileEditForm(instance=profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('profile', username=request.user.username)
        return render(request, self.template_name, {'form': form})