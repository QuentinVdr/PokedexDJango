from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse

# Create your views here.
def index(request):
    return render(request, 'index.html')

def login_user(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/index')
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        print(username, password)
        user = authenticate(request, username=username, password=password)
        print(user)
        if user is not None:
            login(request, user)
            # redirect index
            return HttpResponseRedirect('/index')
        else:
            return render(request, 'authentification/login.html', {'error': 'Invalid Credentials'})
    else:
        return render(request, 'authentification/login.html')
    
def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect('/login')

def register_user(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/index')
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        
        user = User.objects.create_user(username, email, password)
        user.save()
        login(request, user)
        return HttpResponseRedirect('/index')
    else:
        return render(request, 'authentification/register.html')