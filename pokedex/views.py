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
import random
import asyncio


"""
----------------------------------------------------------------------------------
fetch data from pokeapi
----------------------------------------------------------------------------------
"""


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
        all_pokemon = loop.run_until_complete(
            get_pokemon_info_async(data["results"]))
        return all_pokemon
    except RequestException as e:
        raise RequestException(f"Erreur lors de la connexion à l'API : {e}")


async def get_pokemon_info_async(list_pokemon):
    async with aiohttp.ClientSession() as session:
        pokemon_result = []
        tasks = []
        for pokemon in list_pokemon:
            url = pokemon['url']
            cached_pokemon_info = cache.get(url)
            if cached_pokemon_info:
                pokemon_result.append(cached_pokemon_info)
            else:
                tasks.append(get_pokemon_info_async_task(session, pokemon))
        pokemon_result_await = await asyncio.gather(*tasks)
        for pokemon in pokemon_result_await:
            cache.set(pokemon['url'], pokemon, timeout=3600)
            pokemon_result.append(pokemon)
    return pokemon_result


async def get_pokemon_info_async_task(session, pokemon):
    async with session.get(pokemon['url']) as response:
        data = await response.json()
        pokemon_info = transform_pokemon_info_json(data, pokemon['url'])
        return pokemon_info


def transform_pokemon_info_json(pokemon_info, url):
    pokemon_info_transform = {
        'url': url,
        'id': pokemon_info['id'],
        'name': pokemon_info['name'],
        'types': [t['type']['name'] for t in pokemon_info['types']],
        'abilities': [ability['ability']['name'] for ability in pokemon_info['abilities']],
        'stats': {stat['stat']['name']: stat['base_stat'] for stat in pokemon_info['stats']},
        'moves': [move['move']['name'] for move in pokemon_info['moves']],
        'image': pokemon_info['sprites']['front_default'],
        'height': pokemon_info['height'],
        'weight': pokemon_info['weight']
    }
    price = 0
    # calcul price (average of stats)
    for stat in pokemon_info_transform['stats']:
        price += pokemon_info_transform['stats'][stat]
    price = price / len(pokemon_info_transform['stats'])
    price = round(price)
    pokemon_info_transform['price'] = price
    if pokemon_info_transform['image'] is None:
        pokemon_info_transform['image'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png'
    return pokemon_info_transform


def get_all_pokemon_data(request):
    try:
        start_time = time.time()

        cached_pokemon = cache.get('all_pokemon_data')
        all_pokemon = []
        query = ""
        if cached_pokemon:
            print("Données récupérées depuis le cache")
            all_pokemon = cached_pokemon
            query = request.GET.get('search')
            if query:
                all_pokemon = get_filtered_pokemon(query, all_pokemon)

            # get the type filter
            type_filter = request.GET.get('type')
            if type_filter:
                all_pokemon = [
                    pokemon for pokemon in all_pokemon if type_filter.lower() in pokemon['types']]
        else:
            start_fetch_time = time.time()
            all_pokemon = get_all_pokemon()
            cache.set('all_pokemon_data', all_pokemon, timeout=3600)
            # get the search query
            query = request.GET.get('search')
            if query:
                all_pokemon = get_filtered_pokemon(query, all_pokemon)

            # get the type filter
            type_filter = request.GET.get('type')
            if type_filter:
                all_pokemon = [
                    pokemon for pokemon in all_pokemon if type_filter.lower() in pokemon['types']]

            end_fetch_time = time.time()

            end_time = time.time()

            fetch_duration = end_fetch_time - start_fetch_time
            total_duration = end_time - start_time

            print(
                f"Temps pour récupérer les données : {fetch_duration} secondes")
            print(f"Temps total d'exécution : {total_duration} secondes")
        if query == None:
            query = ""

        error = request.session.get('error', '')
        request.session['error'] = ''

        # si l'utilisateur est connecté, on récupère ses pokemons
        if request.user.is_authenticated:
            user = request.user
            userProfil = UserProfile.objects.get(user=user)
            pokemon_user = Pokemon.objects.filter(user=userProfil)
            pokemon_id_api = [
                pokemon.pokemon_api_id for pokemon in pokemon_user]
            return render(request, 'pokedex/index.html', {'pokemon_list': all_pokemon, 'pokemon_user': pokemon_id_api, 'search': query, 'error': error})
        return render(request, 'pokedex/index.html', {'pokemon_list': all_pokemon, 'search': query, 'error': error})
    except Exception as e:
        request.session['error'] = f"Erreur : {e}"
        return render(request, 'pokedex/index.html')


def get_filtered_pokemon(query, all_pokemon):
    return [pokemon for pokemon in all_pokemon if query.lower() in pokemon['name'].lower()]


def get_pokemon_detail(pokemon_id):
    try:
        pokemon_detail_url = f"{API_URL}{pokemon_id}/"
        pokemon_detail = cache.get(pokemon_detail_url)
        if not pokemon_detail:
            pokemon_data = fetch_pokemon_data(pokemon_detail_url)
            pokemon_detail = transform_pokemon_info_json(
                pokemon_data, pokemon_detail_url)
            cache.set(pokemon_detail_url, pokemon_detail, timeout=3600)

        return pokemon_detail
    except Exception as e:
        raise e


def pokemon_detail(request, pokemon_id):
    try:
        pokemon_detail = get_pokemon_detail(pokemon_id)
        url_all_pokemon = f"{API_URL}?limit={10000}"
        all_pokemon = fetch_pokemon_data(url_all_pokemon)
        # find next and prev pokemon id
        index_pokemon = 0
        url_pokemon = pokemon_detail['url']
        for pokemon in all_pokemon['results']:
            if pokemon['url'] == url_pokemon:
                break
            index_pokemon += 1

        next_pokemon_id = None
        prev_pokemon_id = None
        if index_pokemon != 0:
            prev_pokemon_id = get_id_from_url(
                all_pokemon['results'][index_pokemon-1]['url'])
        if index_pokemon != len(all_pokemon['results'])-1:
            next_pokemon_id = get_id_from_url(
                all_pokemon['results'][index_pokemon+1]['url'])
        return render(request, 'pokedex/pokemon_detail.html', {
            'pokemon_detail': pokemon_detail,
            'next_pokemon_id': next_pokemon_id,
            'prev_pokemon_id': prev_pokemon_id,
        })
    except Exception as e:
        request.session['error'] = f"Erreur : {e}"
        return redirect('index')


def get_id_from_url(url):
    return url.split('/')[-2]


"""
----------------------------------------------------------------------------------
login / logout / register
----------------------------------------------------------------------------------
"""


def login_user(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user_mail = User.objects.filter(email=email)
        if not user_mail:
            return render(request, 'authentification/login.html', {'error': 'Email ou mot de passe incorrect', 'email': email})
        username = User.objects.get(email=email).username
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
        user_profil = UserProfile(user=user)
        user_profil.money = 500
        user_profil.save()
        login(request, user)
        return redirect('index')
    else:
        return render(request, 'authentification/register.html')


"""
----------------------------------------------------------------------------------
get all pokemon of the user
----------------------------------------------------------------------------------
"""


# user pokemon list
@login_required(login_url='login')
def user_pokemon_list(request):
    user = request.user
    userProfil = UserProfile.objects.get(user=user)
    pokemons = userProfil.pokemon_set.all().order_by('pokemon_api_id')

    pokemon_api_id = [pokemon.pokemon_api_id for pokemon in pokemons]

    data_url = [{"url": API_URL +
                 str(pokemon.pokemon_api_id)} for pokemon in pokemons]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    all_pokemon = loop.run_until_complete(get_pokemon_info_async(data_url))

    # get the search query
    query = request.GET.get('search')
    if query:
        all_pokemon = get_filtered_pokemon(query, all_pokemon)
    if query == None:
        query = ""

    # get the type filter
    type_filter = request.GET.get('type')
    if type_filter:
        all_pokemon = [
            pokemon for pokemon in all_pokemon if type_filter.lower() in pokemon['types']]

    return render(request, 'pokedex/index.html', {'pokemon_list': all_pokemon, 'disable_buy': True, 'search': query})


"""
----------------------------------------------------------------------------------
User team management
----------------------------------------------------------------------------------
"""

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
            return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter deux fois le même pokemon', 'pokemons': pokemons, 'team_name': team_name, 'pokemon_list_id': pokemon_list_id, 'url_action': 'create_team'})
        if not team_valid:
            return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter un pokemon qui ne vous appartient pas', 'pokemons': pokemons, 'team_name': team_name, 'pokemon_list_id': pokemon_list_id, 'url_action': 'create_team'})
        team.save()
        index = 1
        for pokemon_id in pokemon_list_id:
            # add pokemon to team
            pokemon = Pokemon.objects.get(id=pokemon_id)
            teamPokemon = TeamPokemon(team=team, pokemon=pokemon, order=index)
            teamPokemon.save()
            index += 1
        request.session['success'] = 'Equipe créée'
        return redirect('team_list')
    else:
        return render(request, 'team/createTeam.html', {'pokemons': pokemons, 'url_action': 'create_team'})


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
            team_info["pokemon_"+str(pokemon.order)
                      ]["name"] = pokemon.pokemon.name
            team_info["pokemon_"+str(pokemon.order)
                      ]["id"] = pokemon.pokemon.pokemon_api_id
        list_team.append(team_info)
    print(list_team)
    success = request.session.get('success', '')
    error = request.session.get('error', '')
    request.session['success'] = ''
    request.session['error'] = ''
    return render(request, 'team/listTeam.html', {'list_team': list_team, 'success': success, 'error': error, 'in_fight': user_in_fight(userProfil)})


@login_required(login_url='login')
def delete_team(request, team_id):
    if request.method == "POST":
        team = Team.objects.get(id=team_id)
        user = request.user
        userProfil = UserProfile.objects.get(user=user)
        teams = userProfil.team_set.all()
        team_fight = get_user_fight_in_progress(userProfil)
        if team_fight is not None and (team_fight.team1 == team or team_fight.team2 == team):
            request.session['error'] = 'Vous ne pouvez pas supprimer une équipe en combat'
            return redirect('team_list')
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
        team_fight = get_user_fight_in_progress(userProfil)
        if team_fight is not None and (team_fight.team1 == team or team_fight.team2 == team):
            request.session['error'] = 'Vous ne pouvez pas modifier une équipe en combat'
            return redirect('team_list')
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
                            return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter deux fois le même pokemon', 'pokemons': pokemons, 'team_name': team_name, 'url_action': url_action, 'id_team': team_id})
                    else:
                        return render(request, 'team/createTeam.html', {'error': 'Vous ne pouvez pas ajouter un pokemon qui ne vous appartient pas', 'pokemons': pokemons, 'team_name': team_name, 'url_action': url_action, 'id_team': team_id})
            # delete all pokemon of the team
            TeamPokemon.objects.filter(team=team).delete()
            index = 1
            for pokemon_id in pokemon_list_id:
                # add pokemon to team
                pokemon = Pokemon.objects.get(id=pokemon_id)
                team_pokemon = TeamPokemon(
                    team=team, pokemon=pokemon, order=index)
                team_pokemon.save()
                index += 1
            return redirect('team_list')
        else:
            team_pokemon = team.teampokemon_set.all()
            for pokemon in team_pokemon:
                pokemon_list_id.append(pokemon.pokemon.id)
            return render(request, 'team/createTeam.html', {'url_action': url_action, 'id_team': team_id, 'pokemons': pokemons, 'team_name': team.name, 'pokemon_list_id': pokemon_list_id})
    else:
        request.session['error'] = 'Vous ne pouvez pas modifier cette équipe'
        return redirect('team_list')


def error_404(request, exception):
    return render(request, 'pokedex/404.html', status=404)


def error_404_page(request):
    return render(request, 'pokedex/404.html', status=404)


@login_required(login_url='login')
def buy_pokemon(request):
    if request.method == "POST":
        pokemon_id = request.POST['pokemon_id']
        user = request.user
        user_profil = UserProfile.objects.get(user=user)
        list_pokemon_user = Pokemon.objects.filter(user=user_profil)
        pokemon_user = list_pokemon_user.filter(pokemon_api_id=pokemon_id)
        if pokemon_user:
            request.session['error'] = 'Vous possédez déjà ce pokemon'
            return redirect('index')
        pokemon_info = get_pokemon_detail(pokemon_id)
        if pokemon_info:
            if user_profil.money >= pokemon_info['price']:
                user_profil.money -= pokemon_info['price']
                pokemon = Pokemon(pokemon_api_id=pokemon_id)
                # add pokemon to user
                pokemon.user = user_profil
                pokemon.name = pokemon_info['name']
                pokemon.save()
                user_profil.save()
                return redirect('index')
            else:
                request.session['error'] = 'Vous n\'avez pas assez d\'argent'
                return redirect('index')
        else:
            request.session['error'] = 'Erreur lors de l\'achat'
            return redirect('index')
    else:
        return redirect('index')


"""
----------------------------------------------------------------------------------
Fight
----------------------------------------------------------------------------------
"""


def get_user_fight_in_progress(userProfil):
    # get all fight of the user
    user_team = userProfil.team_set.all()
    # get all fight of the user
    fights1 = Fight.objects.filter(team1__in=user_team, team1_view_win=False)
    fights2 = Fight.objects.filter(team2__in=user_team, team2_view_win=False)

    list_fight = fights1 | fights2
    if list_fight:
        return list_fight[0]
    return None


def user_in_fight(userProfil):
    return get_user_fight_in_progress(userProfil) is not None
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
def register_fight_team(request, team_id):
    if request.method == "POST":
        user = request.user
        userProfil = UserProfile.objects.get(user=user)
        if user_in_fight(userProfil):
            request.session['error'] = 'Vous êtes déjà en combat'
            return redirect('team_list')
        team = Team.objects.get(id=team_id)
        teams = userProfil.team_set.all()
        print(team in teams)
        if team in teams:
            # check if a fight is waiting for a second team
            fights = Fight.objects.filter(team2=None)
            if fights:
                fight = fights[0]
                fight.team2 = team
                # récupérer les données des pokemons des deux équipes
                team1_pokemon = fight.team1.teampokemon_set.all().order_by('order')
                team2_pokemon = fight.team2.teampokemon_set.all().order_by('order')

                # récupérer la vie des pokémons depuis l'api et les stocker dans la base de données
                pokemon1 = Pokemon.objects.get(id=team1_pokemon[0].pokemon.id)
                pokemon2 = Pokemon.objects.get(id=team2_pokemon[0].pokemon.id)
                team1_life = get_pokemon_detail(
                    pokemon1.pokemon_api_id)['stats']['hp']
                team2_life = get_pokemon_detail(
                    pokemon2.pokemon_api_id)['stats']['hp']
                fight.team1_life = team1_life
                fight.team2_life = team2_life
                fight.last_message = "Le combat commence entre " + fight.team1.name + \
                    " et " + fight.team2.name + "!!! Choisissez votre action"
                fight.state = 1
                fight.save()
                return redirect('fight')
            else:
                # create a new fight
                fight = Fight(team1=team)
                fight.save()
            return redirect('fight')
        else:
            return redirect('team_list')
    else:
        return redirect('team_list')


def calcul_fight(userProfil, fight):
    action = ["Attaque", "Défense", "Feinte"]
    if fight is None:
        redirect('team_list')
    if fight.team1_action == 0 or fight.team2_action == 0 or fight.state == 0:
        return

    print(fight.team1_action)
    print(fight.team2_action)
    if fight.team1_action == fight.team2_action:
        print("egalité")
        fight.last_message = "Les deux pokemons ont choisi " + \
            action[fight.team1_action-1] + "!!!"
        fight.team1_action = 0
        fight.team2_action = 0
        fight.save()
        return

    pokemon_team1 = fight.team1.teampokemon_set.filter(
        order=fight.team1_pokemon_number)[0]
    pokemon_team2 = fight.team2.teampokemon_set.filter(
        order=fight.team2_pokemon_number)[0]
    pokemon_team1_detail = get_pokemon_detail(
        pokemon_team1.pokemon.pokemon_api_id)
    pokemon_team2_detail = get_pokemon_detail(
        pokemon_team2.pokemon.pokemon_api_id)

    message = pokemon_team1_detail['name'] + " utilise " + action[fight.team1_action-1] + \
        " et " + pokemon_team2_detail['name'] + \
        " utilise " + action[fight.team2_action-1] + "!!!"

    # pierrre feuille ciseaux
    attack = None
    victim = None
    team1_win = False
    end = False
    if (fight.team1_action == 1 and fight.team2_action == 2) or (fight.team1_action == 2 and fight.team2_action == 3) or (fight.team1_action == 3 and fight.team2_action == 1):
        victim = pokemon_team1_detail
        attack = pokemon_team2_detail
    else:
        victim = pokemon_team2_detail
        attack = pokemon_team1_detail
        team1_win = True
    result = calcul_damage(attack, victim)

    if team1_win:
        fight.team2_life -= result['final_damage']
    else:
        fight.team1_life -= result['final_damage']

    if fight.team2_life <= 0 or fight.team1_life <= 0:
        fight.last_message = message + " " + \
            result['message'] + " " + victim['name'] + " est KO!!!"
        if team1_win:
            fight.team2_pokemon_number += 1
            if fight.team2_pokemon_number > fight.team2.teampokemon_set.count():
                fight.winner = fight.team1
                fight.last_message = fight.team1.user.user.username + \
                    " a gagné le combat!!! Il gagne 50 pokédollars"
                end = True
            else:
                new_pokemon = fight.team2.teampokemon_set.filter(
                    order=fight.team2_pokemon_number)[0]
                new_pokemon_detail = get_pokemon_detail(
                    new_pokemon.pokemon.pokemon_api_id)
                fight.last_message += " " + \
                    new_pokemon_detail['name'] + " entre en jeu!!!"
                fight.team2_life = new_pokemon_detail['stats']['hp']
        else:
            fight.team1_pokemon_number += 1
            if fight.team1_pokemon_number > fight.team1.teampokemon_set.count():
                fight.winner = fight.team2
                fight.last_message = fight.team2.name + \
                    " a gagné le combat!!! Il gagne 50 pokédollars"
                end = True
            else:
                new_pokemon = fight.team1.teampokemon_set.filter(
                    order=fight.team1_pokemon_number)[0]
                new_pokemon_detail = get_pokemon_detail(
                    new_pokemon.pokemon.pokemon_api_id)
                fight.last_message += " " + \
                    new_pokemon_detail['name'] + " entre en jeu!!!"
                fight.team1_life = new_pokemon_detail['stats']['hp']
    else:
        fight.last_message = message + " " + result['message']
    if end:
        fight.state = 2
        fight.team1_view_win = False
        fight.team2_view_win = False
    fight.team1_action = 0
    fight.team2_action = 0
    fight.save()
    return fight


def calcul_damage(pokemon_attack, pokemon_victim):
    result = {
        "message": "",
        "damage": pokemon_attack['stats']['attack'] / 5,
        "damage_reduction": pokemon_attack['stats']['attack'] / 5 * (pokemon_victim['stats']['defense']/8) / 100,
        "final_damage": 0,
        "critical_hit": False,
        "critical_defense": False,
        "dodge": False,
    }
    # attack is the damage of the pokemon
    # defense is used to reduce damage (no critic hit) => reduce to (defense/8) % of damage
    # special attack is the luck to do a critical hit => special (attack/8) % of chance to do a critical hit => attack * 2.2
    # special defense is the luck to do a critical defense => special (defense/8) % of chance to do a critical defense => defense * 2.2
    # speed is the luck to doge an attack => speed (attack/8) % of chance to dodge an attack

    # calcul damage
    damage = pokemon_attack['stats']['attack'] / 5
    critical_hit_chance = random.randint(0, 100)
    if critical_hit_chance <= pokemon_attack['stats']['special-attack']/8:
        result['critical_hit'] = True
        result['damage'] *= 2.2

    # critical defense
    critical_defense_chance = random.randint(0, 100)
    if critical_defense_chance <= pokemon_victim['stats']['special-defense']/8:
        result['critical_defense'] = True
        result['damage_reduction'] = result['damage'] / 2.2

    # dodge
    dodge_chance = random.randint(0, 100)
    if dodge_chance <= pokemon_victim['stats']['speed']/8:
        result['dodge'] = True

    if result['dodge']:
        result['message'] = pokemon_victim['name'] + \
            " a esquivé l'attaque de " + pokemon_attack['name']
        return result

    result['final_damage'] = result['damage'] - result['damage_reduction']
    if result['final_damage'] < 0:
        result['final_damage'] = 0

    if result['critical_hit']:
        result['message'] = pokemon_attack['name'] + " a fait un coup critique sur " + \
            pokemon_victim['name'] + \
            " (⚔️ " + str(round(result['damage'])) + ")"
    else:
        result['message'] = pokemon_attack['name'] + " gagne contre " + \
            pokemon_victim['name'] + \
            " (⚔️ " + str(round(result['damage'])) + ")"

    if result['critical_defense']:
        result['message'] += " mais " + pokemon_victim['name'] + \
            " a fait une défense critique (🛡 "  \
           + str(round(result['damage_reduction'])) + ")"
    else:
        result['message'] += " (🛡 " +\
             str(round(result['damage_reduction'])) + ")"

    result['message'] += " => " + pokemon_victim['name'] + " perd " + \
        str(round(result['final_damage'])) + " points de vie."

    return result


@login_required(login_url='login')
def fight(request):
    user = request.user
    userProfil = UserProfile.objects.get(user=user)
    fight = get_user_fight_in_progress(userProfil)
    can_play = True
    if fight is None:
        request.session['error'] = 'Vous n\'êtes pas en combat'
        return redirect('team_list')

    if fight.team1_pokemon_number > fight.team1.teampokemon_set.count():
        index_team1 = fight.team1.teampokemon_set.count()
    else:
        index_team1 = fight.team1_pokemon_number

    team1 = {"name": fight.team1.name + " (" + fight.team1.user.user.username + ")", "life": fight.team1_life,
             "pokemon": fight.team1.teampokemon_set.filter(order=index_team1)[0].pokemon}
    team2 = {"name": fight.team2.name + " (" + fight.team2.user.user.username +
             ")" if fight.team2 is not None else "En attente d'un adversaire"}
    if not fight.team2:
        can_play = False
    else:
        team2["life"] = fight.team2_life
        index_team2 = 0
        if fight.team2_pokemon_number > fight.team2.teampokemon_set.count():
            index_team2 = fight.team2.teampokemon_set.count()
        else:
            index_team2 = fight.team2_pokemon_number
        team2["pokemon"] = fight.team2.teampokemon_set.filter(order=index_team2)[
            0].pokemon

    if fight.team1.user == userProfil:
        if fight.state == 2:
            fight.team1_view_win = True
            fight.save()
            can_play = False
            print(fight.winner.user)
            print(userProfil)
            if fight.winner.user == userProfil:
                userProfil.money += 50
                userProfil.save()
        elif fight.team2_action == 0 and fight.team1_action != 0:

            return render(request, 'fight/fight.html', {'fight': fight, 'wait_other_player': True, 'can_play': False, 'team1': team1, 'team2': team2})
    elif fight.team2.user == userProfil:
        if fight.state == 2:
            fight.team2_view_win = True
            fight.save()
            can_play = False
            if fight.winner.user == userProfil:
                userProfil.money += 50
                userProfil.save()
        elif fight.team1_action == 0 and fight.team2_action != 0:
            return render(request, 'fight/fight.html', {'fight': fight, 'wait_other_player': True, 'can_play': False, 'team1': team1, 'team2': team2})
    return render(request, 'fight/fight.html', {'fight': fight, 'wait_other_player': fight.team2 == None, 'can_play': can_play, 'team1': team1, 'team2': team2})


@login_required(login_url='login')
def api_fight(request):
    if request.method == "GET":
        user = request.user
        userProfil = UserProfile.objects.get(user=user)
        fight = get_user_fight_in_progress(userProfil)
        if fight is None:
            return JsonResponse({'error': 'Vous n\'êtes pas en combat'})
        if fight.team2 is None:
            return JsonResponse({'can_play': False})
        if fight.team1.user == userProfil and fight.team2_action == 0 and fight.team1_action != 0:
            return JsonResponse({'can_play': False})
        elif fight.team2.user == userProfil and fight.team1_action == 0 and fight.team2_action != 0:
            return JsonResponse({'can_play': False})

        return JsonResponse({'can_play': True})
    return JsonResponse({'error': 'Méthode non autorisée'})


@login_required(login_url='login')
def fight_action(request):
    if request.method == "POST":
        user = request.user
        userProfil = UserProfile.objects.get(user=user)
        fight = get_user_fight_in_progress(userProfil)
        # get the action of the user
        action = request.POST['action']
        try:
            action = int(action)
        except ValueError:
            action = 0
        if action < 1 or action > 3:
            action = 0
        if fight.team1.user == userProfil:
            fight.team1_action = action
        else:
            fight.team2_action = action
        fight.save()
        if fight.team1_action != 0 and fight.team2_action != 0:
            fight = calcul_fight(userProfil, fight)
    return redirect('fight')
