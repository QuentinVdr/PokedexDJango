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

                #récupérer la vie des pokémons depuis l'api et les stocker dans la base de données
                pokemon1 = Pokemon.objects.get(id=team1_pokemon[0].pokemon.id)
                pokemon2 = Pokemon.objects.get(id=team2_pokemon[0].pokemon.id)
                team1_life = get_pokemon_detail(pokemon1.pokemon_api_id)['stats']['hp']
                team2_life = get_pokemon_detail(pokemon2.pokemon_api_id)['stats']['hp']
                fight.team1_life = team1_life
                fight.team2_life = team2_life
                fight.last_message = "Le combat commence entre " + fight.team1.name + " et " + fight.team2.name + "!!! Choisissez votre action"
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
        fight.last_message = "Les deux pokemons ont choisi " + action[fight.team1_action-1] + "!!!"
        fight.team1_action = 0
        fight.team2_action = 0
        fight.save()
        return

    pokemon_team1 = fight.team1.teampokemon_set.filter(order=fight.team1_pokemon_number)[0]
    pokemon_team2 = fight.team2.teampokemon_set.filter(order=fight.team2_pokemon_number)[0]
    pokemon_team1_detail = get_pokemon_detail(pokemon_team1.pokemon.pokemon_api_id)
    pokemon_team2_detail = get_pokemon_detail(pokemon_team2.pokemon.pokemon_api_id)

    message = pokemon_team1_detail['name'] + " utilise " + action[fight.team1_action-1] + " et " + pokemon_team2_detail['name'] + " utilise " + action[fight.team2_action-1] + "!!!"

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
        fight.last_message = message + " " + result['message'] + " " + victim['name'] + " est KO!!!"
        if team1_win:
            fight.team2_pokemon_number += 1
            if fight.team2_pokemon_number > fight.team2.teampokemon_set.count():
                fight.winner = fight.team1
                fight.last_message = fight.team1.user.user.username + " a gagné le combat!!! Il gagne 50 pokédollars"
                end = True
            else:
                new_pokemon = fight.team2.teampokemon_set.filter(order=fight.team2_pokemon_number)[0]
                new_pokemon_detail = get_pokemon_detail(new_pokemon.pokemon.pokemon_api_id)
                fight.last_message += " " + new_pokemon_detail['name'] + " entre en jeu!!!"
                fight.team2_life = new_pokemon_detail['stats']['hp']
        else:
            fight.team1_pokemon_number += 1
            if fight.team1_pokemon_number > fight.team1.teampokemon_set.count():
                fight.winner = fight.team2
                fight.last_message = fight.team2.name + " a gagné le combat!!! Il gagne 50 pokédollars"
                end = True
            else:
                new_pokemon = fight.team1.teampokemon_set.filter(order=fight.team1_pokemon_number)[0]
                new_pokemon_detail = get_pokemon_detail(new_pokemon.pokemon.pokemon_api_id)
                fight.last_message += " " + new_pokemon_detail['name'] + " entre en jeu!!!"
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
        result['message'] = pokemon_victim['name'] + " a esquivé l'attaque de " + pokemon_attack['name']
        return result

    result['final_damage'] = result['damage'] - result['damage_reduction']
    if result['final_damage'] < 0:
        result['final_damage'] = 0
    
    if result['critical_hit']:
        result['message'] = pokemon_attack['name'] + " a fait un coup critique sur " + pokemon_victim['name'] + " (⚔️ " + str(round(result['damage'])) + ")"
    else:
        result['message'] = pokemon_attack['name'] + " gagne contre " + pokemon_victim['name'] + " (⚔️ " + str(round(result['damage'])) + ")"

    if result['critical_defense']:
        result['message'] += " mais " + pokemon_victim['name'] + " a fait une défense critique (🛡 " + str(round(result['damage_reduction'])) + ")"
    else:
        result['message'] += " (🛡 " + str(round(result['damage_reduction'])) + ")"

    result['message'] += " => " + pokemon_victim['name'] + " perd " + str(round(result['final_damage'])) + " points de vie."

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

    team1 = { "name":fight.team1.name + " (" + fight.team1.user.user.username + ")", "life": fight.team1_life, "pokemon": fight.team1.teampokemon_set.filter(order=index_team1)[0].pokemon }
    team2 = { "name":fight.team2.name + " (" + fight.team2.user.user.username + ")" if fight.team2 is not None else "En attente d'un adversaire" }
    if not fight.team2:
        can_play = False
    else:
        team2["life"] = fight.team2_life
        index_team2 = 0
        if fight.team2_pokemon_number > fight.team2.teampokemon_set.count():
            index_team2 = fight.team2.teampokemon_set.count()
        else:
            index_team2 = fight.team2_pokemon_number
        team2["pokemon"] = fight.team2.teampokemon_set.filter(order=index_team2)[0].pokemon


    if fight.team1.user == userProfil:
        if fight.state == 2:
            fight.team1_view_win = True
            fight.save()
            can_play = False
            print(fight.winner.user)
            print(userProfil)
            if fight.winner.user == userProfil:
                print("gagné")
                userProfil.money += 50
                userProfil.save()
        elif fight.team2_action == 0 and fight.team1_action != 0:
            
            return render(request, 'fight/fight.html', {'fight': fight, 'wait_other_player': True, 'can_play': False, 'team1': team1, 'team2': team2})
    elif fight.team2.user == userProfil:
        if fight.state == 2:
            fight.team2_view_win = True
            fight.save()
            can_play = False
            print("aaaaaaaaaaaaaaaaaas")
            if fight.winner.user == userProfil:
                print("gagné")
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

def views_fight_action(request):
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