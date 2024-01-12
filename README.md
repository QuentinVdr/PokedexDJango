![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/b4d7b6ab-4b5c-4a36-9e1f-e0a546bcdb6d)# PokedexDJango

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

## Fonctionnalités
### pokedex
Il est possible d'accéder à l'ensemble des pokémons depuis la page d'acceuil
![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/6c2e22dc-d735-47e6-ba79-5f0015b07e77)

Les détails de chaque pokémons sont accessible en cliquant sur leur carte
![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/b73d6c3a-04af-4d2b-a3b0-a769ec16f1c6)

### recherche
La liste des pokémons peut être filtré en fonction de leurs nom et/ou de leurs type
![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/8a100f5f-c51a-4dcf-a0a4-f14e85bd43f0)

### inscription / connexion
> [!IMPORTANT]
> Pour accéder à l'ensemble des fonctionnalités de l'application, un utilisateur doit s'inscrire/se connecter

![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/475eb672-5686-4a69-bac1-8c5c91d62114)
![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/dfab7762-2405-47f4-a26c-5a895ca109f0)

### gestion de ses pokémons
> [!IMPORTANT]
> Fonctionnalités accessible uniquement pour les utilisateurs connectés

#### achat
Depuis le pokedex (page d'acceuil), un utilisateur peut acheter des pokémons avec des pokédollars (500$ données à l'inscription) (visible à droite dans la barre de navigation)

#### liste
Il est possible d'accéder à la liste des pokémons acheté en cliquant sur "mes pokémons" dans la barre de navigation. Il est possible de filtrer ses pokémons en fonction de leurs nom et/ou de leurs types
![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/63bbeb89-294b-4dd7-8649-7dc80a6e71d4)


### gestion d'équipe de pokémons
> [!IMPORTANT]
> Fonctionnalités accessible uniquement pour les utilisateurs connectés### Combat

#### liste de ses équipes
Il est possible d'accéder à la liste de ses équipes en cliquant sur "mes équipes" dans la barre de navigation. 
![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/d40b4a45-dbc6-4e2f-89a8-81a9c9c7db87)

#### création d'une équipe
Pour créer une nouvelle équipe, il suffit de cliquer sur le bouton "Créer une équipe" dans la page affichant la liste de ses équipes
![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/937e1523-372f-4eeb-ab34-ea45ece41c14)

> [!IMPORTANT]
> Pour créer une équipe, l'utilisateur doit posséder au minimum 6 pokémons
> Un pokémon peut appartenir à plusieurs équipe mais ne peut pas appartenir plusieurs fois à la même équipe

#### modification / suppression d'une équipe
Il est possible de supprimer / modifier une équipe en cliquant sur l'action en question depuis la liste des équipes
> [!IMPORTANT]
> Une équipe en combat ne peut pas être modifié / supprimé

### Combat

#### Règles
Les combats se déroulent en 1 contre 1. Il s'agit d'une variante de pierre-papier-ciseau. Le perdant est celui qui n'a plus de pokémon en vie à la fin
Les deux joueurs choissisent en même temps une action parmi: 
  - Attaquer
  - Se défendre
  - Feinte

Un pokémon qui attaque gagne contre un pokémon qui fait une feinte
Un pokémon qui se défend gagne contre un pokémon qui fait une attaque
Un pokémon qui fait une feinte gagne contre un pokémon qui se protège

Le pokémon qui gagne fait alors des dégats. Les dégats subis dépende de plusieurs statistiques:
- nombre de point de vie => [hp]
- dégats fait à l'adversaire => [attack] / 8
- coup critique => [attack] / 8 * 2.2
-  % de chance de critique => [special-attack] / 8
- dégats réduits => dégats subis (non critique) / 5 * [defense] / 8
- défense critique => dégats réduits * 2.2
- % de chance de défense critique => [special-defense] / 8
- % de chance d'esquiver l'attaque => [speed] / 8

Une fois qu'un pokémon est KO, il est remplacé par le pokémon suivant dans son équipe. Le match se finit quand une des deux équipes n'a plus de pokémons. Le gagnant remporte 50 pokédollars

### lancer un combat
> [!IMPORTANT]
> Un joueur ne peut lancé qu'un combat à la fois

le lancement d'un combat se fait depuis la liste de ses équipes en cliquant sur le bouton "combattre" de l'équipe avec laquelle on souhaite combattre.
> [!IMPORTANT]
> Le combat se lancera uniquement lorsqu'un autre joueur aura également lancé un combat
> ![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/60ed0ed7-f55d-4ad2-bbb4-5f2c716730c4)

#### reprendre un combat
Pour reprendre un combat précédemment lancé, il faut cliquer sur le boutton "Retourner au combat" accessible dans "mes équipes"
![image](https://github.com/QuentinVdr/PokedexDJango/assets/93726221/688d9081-0c4e-4dc3-8592-d1be5afe3d7a)





