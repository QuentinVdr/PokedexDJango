from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from .models import UserProfile, TeamPokemon, Pokemon, Team, Fight
from django.contrib.auth.decorators import login_required
import re

def index(request):
    return render(request, 'index.html')

# login page
def login_user(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        username = User.objects.get(email=email).username
        if not username:
            return render(request, 'authentification/login.html', {'error': 'Email ou mot de passe incorrect', 'email': email})
        user = authenticate(request, username=username, password=password)
        user_redirection = request.POST.get('next', '/')
        if user is not None:
            login(request, user)
            if user_redirection and user_redirection.startswith('/'):
                return redirect(user_redirection)
            return redirect('index')
        else:
            return render(request, 'authentification/login.html', {'error': 'Email ou mot de passe incorrect', 'email': email})
    else:
        next_url = request.GET.get('next', '')
        if next_url and next_url.startswith('/'):
            return render(request, 'authentification/login.html', {'next': next_url})
        else:
            return render(request, 'authentification/login.html')
    
# logout page (redirect to login page)
@login_required(login_url='login', redirect_field_name='')
def logout_user(request):
    if request.method == "POST":
        logout(request)
        return redirect('login')
    else:
        return redirect('index')

def register_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        regex_password = r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"
        if not re.match(regex_password, password):
            return render(request, 'authentification/register.html', {'error': 'Le mot de passe doit contenir au moins 8 caractères dont au moins une lettre et un chiffre', 'username': username, 'email': email})
        
        # check if username or email already exist
        if User.objects.filter(username=username).exists():
            return render(request, 'authentification/register.html', {'error': 'Le nom d\'utilisateur existe déjà', 'email': email})
        if User.objects.filter(email=email).exists():
            return render(request, 'authentification/register.html', {'error': 'L\'email existe déjà', 'username': username})
        user = User.objects.create_user(username, email, password)
        user.save()
        # create user profile
        userProfil = UserProfile(user=user)
        userProfil.save()
        login(request, user)
        # redirect to route name "index"
        return redirect('index')
    else:
        return render(request, 'authentification/register.html')
    
# user pokemon list
@login_required(login_url='login')
def user_pokemon_list(request):
    user = request.user
    userProfil = UserProfile.objects.get(user=user)
    pokemons = userProfil.pokemon_set.all()
    return render(request, 'pokemon/myPokemon.html', {'pokemons': pokemons})
    
# user create team
@login_required(login_url='login')
def new_team(request):
    # check if user has already in fight
    user = request.user
    userProfil = UserProfile.objects.get(user=user)
    # get all fight of the user
    pokemons = userProfil.pokemon_set.all()
    if user_in_fight(userProfil):
        return redirect('fight_history')
    if request.method == "POST":
        team_name = request.POST['team_name']
        team = Team(name=team_name, user=userProfil)
        pokemon_list_id = []
        for i in range(1, 7):
            pokemon_id = request.POST['pokemon_'+str(i)]
            if pokemon_id:
                # check if user has this pokemon or selected pokemon is not already in the team
                pokemon = Pokemon.objects.get(id=pokemon_id)
                if pokemon.user == userProfil:
                    if pokemon_id not in pokemon_list_id:
                        pokemon_list_id.append(pokemon_id)
                    else:
                        return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter deux fois le même pokemon', 'pokemons': pokemons, 'team_name': team_name})
                else:
                    return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter un pokemon qui ne vous appartient pas', 'pokemons': pokemons, 'team_name': team_name})
        team.save()
        index = 1
        for pokemon_id in pokemon_list_id:
            # add pokemon to team
            pokemon = Pokemon.objects.get(id=pokemon_id)
            teamPokemon = TeamPokemon(team=team, pokemon=pokemon, order=index)
            teamPokemon.save()
            index += 1
        # create fight
        fight = Fight(team1=team)
        fight.save()

        return redirect('index')
    else:
        return render(request, 'team/createTeam.html', {'pokemons': pokemons})


def user_in_fight(userProfil):
    # get all fight of the user
    user_team = userProfil.team_set.all()
    fights = Fight.objects.filter(team1__in=user_team)
    # if fight is not finished (winner is null)
    in_fight = False
    for fight in fights:
        if fight.winner is None:
            in_fight = True
    return in_fight

# fight history
@login_required(login_url='login')
def fight_history(request):
    user = request.user
    userProfil = UserProfile.objects.get(user=user)
    # get all fight of the user
    user_team = userProfil.team_set.all()
    fights = Fight.objects.filter(team1__in=user_team)
    list_fight = []
    in_fight = False
    for fight in fights:
        user_win = False
        if fight.winner is not None:
            if fight.winner in user_team:
                user_win = True
        else:
            in_fight = True
        date = fight.date.strftime("%d/%m/%Y %H:%M:%S")
        team_user = fight.team1 if fight.team1 in user_team else fight.team2
        team_opponent = fight.team1 if fight.team1 not in user_team else fight.team2 if fight.team2 is not None else ""
        fight_info = {
            "date": date,
            "win": user_win,
            "team_user": team_user,
            "team_opponent": team_opponent,
            "finish": fight.winner is not None
        }
        print(fight_info)
        list_fight.append(fight_info)
    print(fights)
    print(list_fight)
    return render(request, 'fight/history.html', {'list_fight': list_fight, 'in_fight': in_fight})

