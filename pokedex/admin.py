from django.contrib import admin
from .models import Pokemon, UserProfile, TeamPokemon, Team, Fight

admin.site.register(Pokemon)
admin.site.register(UserProfile)
admin.site.register(TeamPokemon)
admin.site.register(Team)
admin.site.register(Fight)
