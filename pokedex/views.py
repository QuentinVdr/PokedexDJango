from django.core.cache import cache
import requests
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from requests.exceptions import RequestException
from settings import *
import time
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from .models import UserProfile, TeamPokemon, Pokemon, Team, Fight
from django.contrib.auth.decorators import login_required
import re


def fetch_pokemon_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        raise RequestException(f"Erreur lors de la connexion à l'API : {e}")


def get_pokemon_info(url):
    cached_pokemon_info = cache.get(url)
    if cached_pokemon_info:
        return cached_pokemon_info

    pokemon_data = fetch_pokemon_data(url)
    pokemon_info = {
        'name': pokemon_data['name'],
        'types': [t['type']['name'] for t in pokemon_data['types']],
        'abilities': [ability['ability']['name'] for ability in pokemon_data['abilities']],
        'stats': {stat['stat']['name']: stat['base_stat'] for stat in pokemon_data['stats']},
        'moves': [move['move']['name'] for move in pokemon_data['moves']],
        'image': pokemon_data['sprites']['front_default']
    }

    cache.set(url, pokemon_info, timeout=3600)
    return pokemon_info


def get_pokemon_batch(url):
    try:
        data = fetch_pokemon_data(url)
        pokemon_batch = []
        for pokemon in data['results']:
            pokemon_info = get_pokemon_info(pokemon['url'])
            pokemon_batch.append(pokemon_info)

        return pokemon_batch, data.get('next')
    except RequestException as e:
        raise RequestException(f"Erreur lors de la connexion à l'API : {e}")


def get_all_pokemon(batch_size=100000):
    try:
        all_pokemon = []
        offset = 0

        while True:
            gen_url = f"{API_URL}?limit={121}&offset={offset}"
            data = fetch_pokemon_data(gen_url)

            for pokemon in data['results']:
                pokemon_info = get_pokemon_info(pokemon['url'])
                all_pokemon.append(pokemon_info)

            if not data.get('next'):
                break
            offset += batch_size * 5

        return all_pokemon
    except RequestException as e:
        raise RequestException(f"Erreur lors de la connexion à l'API : {e}")


def get_all_pokemon_data(request):
    try:
        start_time = time.time()

        cached_pokemon = cache.get('all_pokemon_data')

        if cached_pokemon:
            return render(request, 'pokedex/index.html', {'pokemon_list': cached_pokemon})
        else:
            start_fetch_time = time.time()
            all_pokemon = get_all_pokemon()
            end_fetch_time = time.time()

            cache.set('all_pokemon_data', all_pokemon, timeout=3600)
            end_time = time.time()

            fetch_duration = end_fetch_time - start_fetch_time
            total_duration = end_time - start_time

            print(f"Temps pour récupérer les données : {fetch_duration} secondes")
            print(f"Temps total d'exécution : {total_duration} secondes")

            return render(request, 'pokedex/index.html', {'pokemon_list': all_pokemon})
    except Exception as e:
        return render(request, 'pokedex/errors.html', {'error_message': f"Erreur : {e}"})


def get_filtered_pokemon(query, all_pokemon):
    return [pokemon for pokemon in all_pokemon if query.lower() in pokemon['name'].lower()]


def search_pokemon(request):
    try:
        query = request.GET.get('search')
        all_pokemon = cache.get('all_pokemon_data')

        if query and all_pokemon:
            cached_results = cache.get(query)
            if cached_results:
                filtered_pokemon = cached_results
            else:
                filtered_pokemon = get_filtered_pokemon(query, all_pokemon)
                cache.set(query, filtered_pokemon, timeout=3600)

            return render(request, 'pokedex/index.html', {'pokemon_list': filtered_pokemon, 'query': query})
        else:
            return render(request, 'pokedex/index.html', {'pokemon_list': all_pokemon})
    except Exception as e:
        return render(request, 'pokedex/errors.html', {'error_message': f"Erreur : {e}"})

def filter_pokemon_by_type(request):
    try:
        type_filter = request.GET.get('type')
        all_pokemon = cache.get('all_pokemon_data')

        if type_filter and all_pokemon:
            filtered_pokemon = [pokemon for pokemon in all_pokemon if type_filter.lower() in pokemon['types']]
            return render(request, 'pokedex/index.html', {'pokemon_list': filtered_pokemon, 'query': type_filter})
        else:
            return HttpResponseRedirect(reverse('get_all_pokemon_data'))  # Redirige vers la liste complète si aucun filtre
    except Exception as e:
        return render(request, 'pokedex/errors.html', {'error_message': f"Erreur : {e}"})

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

