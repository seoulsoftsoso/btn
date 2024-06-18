from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
import json
def csrf(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrf_token': csrf_token})

@csrf_exempt  # Exempt this view from CSRF protection for simplicity
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Authentication successful
            return JsonResponse({'success': True})
        else:
            # Authentication failed
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt  # Exempt this view from CSRF protection for simplicity
def userdata(request):
    if request.method == 'GET':
        # Assuming you have a way to get the authenticated user
        # (e.g., from the access token provided in the request headers)
        user = request.user

        # Serialize user data to JSON
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            # Add any other user data you want to include
        }

        return JsonResponse(user_data)

    return JsonResponse({'error': 'Invalid request method'}, status=400)