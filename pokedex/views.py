from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from .models import UserProfile
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
    # get all pokemon of the user
    user = request.user
    userProfil = UserProfile.objects.get(user=user)
    pokemons = userProfil.pokemon_set.all()
    if request.method == "POST":
        team_name = request.POST['team_name']
        
        team = Team(name=team_name, user=userProfil)
        team.save()
        return redirect('index')
    else:
        return render(request, 'team/createTeam.html')