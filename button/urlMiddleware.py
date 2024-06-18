from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin

class LoginRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            current_url = resolve(request.path_info).url_name
            login_exempt_urls = getattr(settings, 'LOGIN_EXEMPT_URLS', [])
            print(current_url, login_exempt_urls)
            if current_url not in login_exempt_urls:
                return redirect(settings.LOGIN_URL)