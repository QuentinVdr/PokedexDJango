from django.urls import path
from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from pokedex import views

urlpatterns = [
   path('', views.get_all_pokemon_data, name='index'),
   path('search/', views.search_pokemon, name='search_pokemon'),
   path('filter/', views.filter_pokemon_by_type, name='filter_pokemon_by_type'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('pokemon/user/', views.user_pokemon_list, name='user_pokemon_list'),
    path('team/manage/', views.new_team, name='create_team'),
    path('team/list/', views.team_list, name='team_list'),
    path('team/manage/<int:team_id>/', views.update_team, name='update_team'),
    path('team/delete/<int:team_id>/', views.delete_team, name='delete_team'),
    # path('fight/history/', views.fight_history, name='fight_history'),
    # error 404
    path('404/', views.error_404_page, name='error_404'),
]

urlpatterns += staticfiles_urlpatterns()
