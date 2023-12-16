from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin


class UserProfile(models.Model):
    # information supplémentaire sur l'utilisateur (argent, ...)
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    money = models.IntegerField(default=0)
    
    def __str__(self):
        return self.user.username
    
class Pokemon(models.Model):
    pokemon_api_id = models.IntegerField()
    name = models.CharField(max_length=200)
    # team of the pokemon (null if not in a team)

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class TeamPokemon(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    order = models.IntegerField()
    
    def __str__(self):
        return self.team.name + " - " + self.pokemon.name

class Fight(models.Model):
    # team of the pokemon (null if not in a team)
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team2', null=True, blank=True) # null if fight not started (waiting for a second team)
    winner = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='winner', null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    turn = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='turn', null=True, blank=True)
    
    def __str__(self):
        return str(self.date)