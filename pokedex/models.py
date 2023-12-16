from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin


class UserProfile(models.Model):
    # information supplémentaire sur l'utilisateur (argent, ...)
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    money = models.IntegerField(default=0)
    
    def __str__(self):
        return self.user.username

class Team(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
class Pokemon(models.Model):
    pokemon_api_id = models.IntegerField()
    name = models.CharField(max_length=200)
    # team of the pokemon (null if not in a team)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    number = models.IntegerField(default=0, null=True, blank=True) # number in team (null if not in a team)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
