from django.core.cache import cache
import requests
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
import aiohttp
import asyncio


def fetch_pokemon_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        raise RequestException(f"Erreur lors de la connexion à l'API : {e}")

def get_all_pokemon():
    try:
        all_pokemon = []
        gen_url = f"{API_URL}?limit={10000}"
        data = fetch_pokemon_data(gen_url)
        # async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        all_pokemon = loop.run_until_complete(get_pokemon_info_async(data["results"]))

        print(f"Nombre de pokemon récupérés : {len(all_pokemon)}")
        print(f"Nombre de pokemon en cache : {len(cache._cache)}")

        return all_pokemon
    except RequestException as e:
        raise RequestException(f"Erreur lors de la connexion à l'API : {e}")

async def get_pokemon_info_async(list_pokemon):
    result = []
    for pokemon in list_pokemon:
        if 'url' in pokemon and pokemon['url'] in cache._cache:
            result.append(cache.get(pokemon['url']))
            list_pokemon.remove(pokemon)

    async with aiohttp.ClientSession() as session:
        cacheCount = 0
        notCacheCount = 0
        tasks = []
        for pokemon in list_pokemon:
            url = pokemon['url']
            cached_pokemon_info = cache.get(url)
            if cached_pokemon_info:
                cacheCount += 1
                tasks.append(cached_pokemon_info)
            else:
                notCacheCount += 1
                tasks.append(get_pokemon_info_async_task(session, pokemon))
        print(f"Nombre de pokemon en cache : {cacheCount}")
        print(f"Nombre de pokemon non en cache : {notCacheCount}")
        print(f"Total : {cacheCount + notCacheCount}")
        result.extend(await asyncio.gather(*tasks))
    for pokemon in result:
        cache.set(pokemon['url'], pokemon, timeout=3600)
    return result
    
async def get_pokemon_info_async_task(session, pokemon):
    async with session.get(pokemon['url']) as response:
        data = await response.json()
        pokemon_info = {
            'url': pokemon['url'],
            'id': data['id'],
            'name': data['name'],
            'types': [t['type']['name'] for t in data['types']],
            'abilities': [ability['ability']['name'] for ability in data['abilities']],
            'stats': {stat['stat']['name']: stat['base_stat'] for stat in data['stats']},
            'moves': [move['move']['name'] for move in data['moves']],
            'image': data['sprites']['front_default'],
            'height': data['height'],
            'weight': data['weight'],
        }
        return pokemon_info

def get_all_pokemon_data(request):
    try:
        start_time = time.time()

        cached_pokemon = cache.get('all_pokemon_data')

        if cached_pokemon:
            print("Données récupérées depuis le cache")
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
        if query is None:
            return redirect('index')
        all_pokemon = cache.get('all_pokemon_data')
        if all_pokemon is None:
            all_pokemon = get_all_pokemon()
            cache.set('all_pokemon_data', all_pokemon, timeout=3600)


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
        print(type_filter)
        if type_filter is None:
            return redirect('index')
        all_pokemon = cache.get('all_pokemon_data')
        if all_pokemon is None:
            all_pokemon = get_all_pokemon()
            cache.set('all_pokemon_data', all_pokemon, timeout=3600)

        if type_filter and all_pokemon:
            filtered_pokemon = [pokemon for pokemon in all_pokemon if type_filter.lower() in pokemon['types']]
            return render(request, 'pokedex/index.html', {'pokemon_list': filtered_pokemon, 'query': type_filter})
        else:
            return HttpResponseRedirect(reverse('get_all_pokemon_data'))
    except Exception as e:
        return render(request, 'pokedex/errors.html', {'error_message': f"Erreur : {e}"})

def get_pokemon_detail(pokemon_id):
    try:
        pokemon_detail_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/"
        pokemon_detail = cache.get(pokemon_detail_url)
        if not pokemon_detail:
            pokemon_data = fetch_pokemon_data(pokemon_detail_url)
            pokemon_detail = get_pokemon_info(pokemon_data)
            cache.set(pokemon_detail_url, pokemon_detail, timeout=3600)

        return pokemon_detail
    except Exception as e:
        raise e  # Gérez les erreurs selon vos besoins

def pokemon_detail(request, pokemon_id):
    try:
        pokemon_detail = get_pokemon_detail(pokemon_id)
        return render(request, 'pokedex/pokemon_detail.html', {'pokemon_detail': pokemon_detail})
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
    if request.method == "POST":
        team_name = request.POST['team_name']
        team = Team(name=team_name, user=userProfil)
        pokemon_list_id = []
        team_valid = True
        for i in range(1, 7):
            pokemon_id = request.POST['pokemon_'+str(i)]
            if pokemon_id:
                # check if user has this pokemon or selected pokemon is not already in the team
                pokemon = Pokemon.objects.get(id=pokemon_id)
                if pokemon.user == userProfil:
                    try:
                        if int(pokemon_id) not in pokemon_list_id:
                            pokemon_list_id.append(int(pokemon_id))
                    except ValueError:
                        pass
                else:
                    team_valid = False
        if len(pokemon_list_id) != 6:
            return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter deux fois le même pokemon', 'pokemons': pokemons, 'team_name': team_name, 'pokemon_list_id': pokemon_list_id, 'url_action' : 'create_team'})
        if not team_valid:
            return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter un pokemon qui ne vous appartient pas', 'pokemons': pokemons, 'team_name': team_name, 'pokemon_list_id': pokemon_list_id, 'url_action' : 'create_team'})
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
        request.session['success'] = 'Equipe créée'
        return redirect('team_list')
    else:
        return render(request, 'team/createTeam.html', {'pokemons': pokemons, 'url_action' : 'create_team'})

@login_required(login_url='login')
def team_list(request):
    user = request.user
    userProfil = UserProfile.objects.get(user=user)
    teams = userProfil.team_set.all()
    list_team = []
    for team in teams:
        team_info = {
            "name": team.name,
            "id": team.id
        }
        team_pokemon = team.teampokemon_set.all()
        for pokemon in team_pokemon:
            team_info["pokemon_"+str(pokemon.order)] = {}
            team_info["pokemon_"+str(pokemon.order)]["name"] = pokemon.pokemon.name
            team_info["pokemon_"+str(pokemon.order)]["id"] = pokemon.pokemon.pokemon_api_id
        list_team.append(team_info)
    print(list_team)
    success = request.session.get('success', '')
    error = request.session.get('error', '')
    request.session['success'] = ''
    request.session['error'] = ''
    return render(request, 'team/listTeam.html', {'list_team': list_team, 'success': success, 'error': error})


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

@login_required(login_url='login')
def delete_team(request, team_id):
    if request.method == "POST":
        team = Team.objects.get(id=team_id)
        user = request.user
        userProfil = UserProfile.objects.get(user=user)
        teams = userProfil.team_set.all()
        if team in teams:
            team.delete()
            request.session['success'] = 'Equipe supprimée'
            return redirect('team_list')
        else:
            request.session['error'] = 'Vous ne pouvez pas supprimer cette équipe'
            return redirect('team_list')
    else:
        return redirect('team_list')


@login_required(login_url='login')
def update_team(request, team_id):
    team = Team.objects.get(id=team_id)
    user = request.user
    userProfil = UserProfile.objects.get(user=user)
    teams = userProfil.team_set.all()
    pokemons = userProfil.pokemon_set.all()
    pokemon_list_id = []

    # url_action = 'update_team' and the id of the team
    url_action = 'update_team'
    if team in teams:
        if request.method == "POST":
            team_name = request.POST['team_name']
            team.name = team_name
            team.save()
            for i in range(1, 7):
                pokemon_id = request.POST['pokemon_'+str(i)]
                if pokemon_id:
                    # check if user has this pokemon or selected pokemon is not already in the team
                    pokemon = Pokemon.objects.get(id=pokemon_id)
                    if pokemon.user == userProfil:
                        if pokemon_id not in pokemon_list_id:
                            pokemon_list_id.append(pokemon_id)
                        else:
                            return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter deux fois le même pokemon', 'pokemons': pokemons, 'team_name': team_name, 'url_action' : url_action, 'id_team': team_id})
                    else:
                        return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter un pokemon qui ne vous appartient pas', 'pokemons': pokemons, 'team_name': team_name, 'url_action' : url_action, 'id_team': team_id})
            # delete all pokemon of the team
            TeamPokemon.objects.filter(team=team).delete()
            index = 1
            for pokemon_id in pokemon_list_id:
                # add pokemon to team
                pokemon = Pokemon.objects.get(id=pokemon_id)
                teamPokemon = TeamPokemon(team=team, pokemon=pokemon, order=index)
                teamPokemon.save()
                index += 1
            return redirect('team_list')
        else:
            team_pokemon = team.teampokemon_set.all()
            for pokemon in team_pokemon:
                pokemon_list_id.append(pokemon.pokemon.id)
            return render(request, 'team/createTeam.html', {'url_action' : url_action, 'id_team': team_id, 'pokemons': pokemons, 'team_name': team.name, 'pokemon_list_id': pokemon_list_id})
    else:
        request.session['error'] = 'Vous ne pouvez pas modifier cette équipe'
        return redirect('team_list')
    
def error_404(request, exception):
    return render(request, 'pokedex/404.html', status=404)

def error_404_page(request):
    return render(request, 'pokedex/404.html', status=404)