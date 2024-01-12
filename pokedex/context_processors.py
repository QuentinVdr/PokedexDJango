from .models import UserProfile

# method global for get money of user
def get_money(request):
    if request.user.is_authenticated:
        # récupérer le profil de l'utilisateur s'il existe, sinon le créer
        user = None
        try:
            user = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            user = UserProfile(user=request.user, money=500)
            user.save()
        return {'money': user.money}
    else:
        return {'money': 0}