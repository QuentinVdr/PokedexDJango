import requests
from django.shortcuts import render
from settings import *

def get_all_pokemon(request):

    print(API_URL)

    base_url = API_URL

    all_pokemon_names = []

    next_page = base_url
    while next_page:
        response = requests.get(next_page)

        if response.status_code == 200:
            pokemon_data = response.json()
            results = pokemon_data.get('results', [])
            pokemon_names = [pokemon['name'] for pokemon in results]
            all_pokemon_names.extend(pokemon_names)
            next_page = pokemon_data.get('next')
        else:
            error_message = "La requête à l'API PokeAPI a échoué."
            return render(request, 'pokedex/errors.html', {'error_message': error_message})

    return render(request, 'pokedex/index.html', {'pokemon_names': all_pokemon_names})
