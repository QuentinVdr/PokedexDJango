# PokedexDJango

## Technologies
- Framework : [Django](https://www.djangoproject.com/)
- Framework CSS : [Tailwind](https://tailwindcss.com/)
- API : [PokeApi](https://pokeapi.co/)

## Installation
- Clone the repository
```bash
git clone https://github.com/QuentinVdr/PokedexDJango.git
```
- Create a virtual environment
```bash
python -m venv ./venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source ./venv/bin/activate
```
- Install the dependencies
```bash
pip install -r requirements.txt
```
- Run the server
```bash
python manage.py runserver
```

> **_NOTE:_**  Don't forget to update the requirements.txt file if you install a new package with
> ```bash
> pip freeze > requirements.txt
> ```

## Features
- [ ] List of all pokemons
- [ ] Search bar
  - [ ] Pokemon name
  - [ ] Pokemon generation
  - [ ] Pokemon type
- [ ] Pokemon details
  - [ ] Pokemon types
  - [ ] Pokemon evolution
  - [ ] Pokemon stats
  - [ ] Pokemon moves
  - [ ] Pokemon abilities
- [ ] Pokemon combat
  - [ ] PvP local
  - [ ] PvE
  - [ ] Pokemon coin earning
- [ ] Manage user
  - [ ] Login
  - [ ] Register
  - [ ] Logout
  - [ ] Change password
  - [ ] Change username
  - [ ] Delete account
- [ ] Manage your team
  - [ ] Add a pokemon
  - [ ] Remove a pokemon
  - [ ] Rename a pokemon
  - [ ] Change the order of your team
- [ ] Pokemon shop
  - [ ] Buy Pokemon
  - [ ] Sell Pokemon
  - [ ] Buy Potion
