from django.shortcuts import redirect
from django.contrib import messages

PANEL_EXEMPT = {'/panel/login/', '/panel/logout/'}


class AdminPanelGuardMiddleware:
    """Block every /panel/* URL for non-staff users at the middleware level."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/panel/') and request.path not in PANEL_EXEMPT:
            if not request.user.is_authenticated:
                return redirect('/panel/login/')
            if not request.user.is_staff:
                messages.error(request, 'Access denied. Admin panel is for authorised staff only.')
                return redirect('/shop/')
        return self.get_response(request)
