from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class AdminSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/admin/'):
            # Use a different session cookie name for the admin
            request.session = request.session._get_session_from_db()
            request.session.save()
            request.session = request.session._get_session_from_db(settings.ADMIN_SESSION_COOKIE_NAME)
        else:
            # Default session for non-admin users
            request.session = request.session._get_session_from_db(settings.SESSION_COOKIE_NAME)

    def process_response(self, request, response):
        if request.path.startswith('/admin/'):
            response.set_cookie(
                settings.ADMIN_SESSION_COOKIE_NAME,
                request.session.session_key,
                max_age=settings.SESSION_COOKIE_AGE,
                httponly=True,
                secure=request.is_secure(),
                samesite='Lax',
            )
        else:
            response.set_cookie(
                settings.SESSION_COOKIE_NAME,
                request.session.session_key,
                max_age=settings.SESSION_COOKIE_AGE,
                httponly=True,
                secure=request.is_secure(),
                samesite='Lax',
            )
        return response
