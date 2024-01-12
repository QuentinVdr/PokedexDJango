# PokedexDJango

## Technologies
- Framework : [Django](https://www.djangoproject.com/)
- Framework CSS : [Tailwind](https://tailwindcss.com/)
- API : [PokeApi](https://pokeapi.co/)

## Installation
- Cloner le répertoire 
```bash
git clone https://github.com/QuentinVdr/PokedexDJango.git
```
- Crée un environnement virtuel
```bash
python -m venv ./venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source ./venv/bin/activate
```
- Installer les dépendances
```bash
pip install -r requirements.txt
```

- Installer la base de données
```
python manage.py migrate
```


- Démarrer le serveur
```bash
python manage.py runserver
```
