from django.urls import path
from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from pokedex import views

urlpatterns = [
   path('', views.get_all_pokemon_data, name='index'),
   path('login/', views.login_user, name='login'),
   path('logout/', views.logout_user, name='logout'),
   path('register/', views.register_user, name='register'),
   path('pokemon/user/', views.user_pokemon_list, name='user_pokemon_list'),
   path('team/manage/', views.new_team, name='create_team'),
   path('team/list/', views.team_list, name='team_list'),
   path('team/manage/<int:team_id>/', views.update_team, name='update_team'),
   path('team/delete/<int:team_id>/', views.delete_team, name='delete_team'),
   path('team/registerfight/<int:team_id>/', views.register_fight_team, name='register_fight'),
   path('fight/', views.fight, name='fight'),
   path('fight/action/', views.fight_action, name='fight_action'),
   path('pokemon/detail/<int:pokemon_id>/', views.pokemon_detail, name='detail_pokemon'),
   path('pokemon/buy/', views.buy_pokemon, name='buy_pokemon'),
   path('pokemon/detail/prev/<int:pokemon_id>/', views.pokemon_detail, name='prev_pokemon_detail'),
   path('pokemon/detail/next/<int:pokemon_id>/', views.pokemon_detail, name='next_pokemon_detail'),
   path('api/fight/', views.api_fight, name='api_fight'),
]

urlpatterns += staticfiles_urlpatterns()
