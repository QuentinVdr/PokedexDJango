from django.urls import path

from pokedex import views

urlpatterns = [
    path('', views.get_all_pokemon, name='index')
]
