from django.shortcuts import redirect
from PokedexDJango.settings import DEBUG
from django.urls import resolve

class RedirectionManagerMiddleware:
    """
    Middleware to manage redirection (redirect to index if user is logged and try to access login or register page)
    """
    def __init__(self, get_response):
        self.PAGE_REDIRECT_USER_LOGGED = ['login', 'register']
        self.get_response = get_response

    def __call__(self, request):
        # vérifier si l'utilisateur est sur une route définie dont le nom dans urls.py correspond à PAGE_REDIRECT_USER_LOGGED
        resolved_url = resolve(request.path_info)
        name = resolved_url.url_name
        if DEBUG:
            print("RedirectionManagerMiddleware: ", name)
        if request.user.is_authenticated and name in self.PAGE_REDIRECT_USER_LOGGED:
            return redirect('index')
        response = self.get_response(request)
        return response

