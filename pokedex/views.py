from django.core.cache import cache
import requests
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from requests.exceptions import RequestException
from settings import *
import time


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
