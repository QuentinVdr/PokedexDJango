from django.urls import path

from pokedex import views

urlpatterns = [
   path('', views.get_all_pokemon_data, name='index'),
   path('search/', views.search_pokemon, name='search_pokemon'),
   path('filter/', views.filter_pokemon_by_type, name='filter_pokemon_by_type'),
]
