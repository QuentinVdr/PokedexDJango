from .models import UserProfile

# method global for get money of user
def get_money(request):
    if request.user.is_authenticated:
        user = UserProfile.objects.get(user=request.user)
        return {'money': user.money}
    else:
        return {'money': 0}