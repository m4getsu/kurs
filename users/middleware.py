from django.shortcuts import redirect
from django.utils import timezone


class BanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path != '/banned/':
            try:
                profile = request.user.profile
                if profile.is_banned:
                    if not profile.banned_until or profile.banned_until > timezone.now():
                        return redirect('banned')
                    else:
                        profile.is_banned = False
                        profile.banned_until = None
                        profile.ban_reason = None
                        profile.save()
            except Exception:
                pass

        return self.get_response(request)


class LastSearchMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from urllib.parse import unquote
        request.last_search = unquote(request.COOKIES.get('last_search', ''))
        return self.get_response(request)
