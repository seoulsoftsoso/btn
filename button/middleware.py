from django.shortcuts import redirect
from django.urls import reverse

class EnsureUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            return self.get_response(request)
        
        if request.path.startswith('/register/'):
            return self.get_response(request)

        if not request.user.is_authenticated and request.path != '/auth/login/' and request.path != '/':
            return redirect('/')

        response = self.get_response(request)
        return response
