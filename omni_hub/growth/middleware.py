import os
from django.http import JsonResponse
from django.shortcuts import redirect

class OmniAuthMiddleware:
    """
    Guarantees private, password-protected access to Omni Hub.
    Prevents unauthorized devices on the local IP / network from accessing the dashboard or APIs.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Whitelisted paths that do not require authentication:
        # - Login page & login API
        # - Logout endpoints
        # - Static assets (CSS, JS, fonts, images)
        # - Health ping for watchdog/uptime checks
        EXEMPT_PATHS = [
            '/login/',
            '/logout/',
            '/api/auth/login/',
            '/api/auth/logout/',
            '/api/health/',
            '/static/',
            '/favicon.ico',
        ]

        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return self.get_response(request)

        # Check authentication:
        is_auth = (
            request.session.get('omni_auth_verified') is True or
            (hasattr(request, 'user') and request.user.is_authenticated)
        )

        if not is_auth:
            if path.startswith('/api/'):
                return JsonResponse({
                    "status": "unauthorized",
                    "message": "Authentication required. Please unlock at /login/",
                    "login_url": "/login/"
                }, status=401)
            else:
                return redirect(f"/login/?next={path}")

        return self.get_response(request)

