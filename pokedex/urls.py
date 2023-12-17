from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('pokemon/user/', views.user_pokemon_list, name='user_pokemon_list'),
    path('team/manage/', views.new_team, name='create_team'),
    path('team/list/', views.team_list, name='team_list'),
    path('team/manage/<int:team_id>/', views.update_team, name='update_team'),
    path('team/delete/<int:team_id>/', views.delete_team, name='delete_team'),
    path('fight/history/', views.fight_history, name='fight_history'),

]

urlpatterns += staticfiles_urlpatterns()
