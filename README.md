# Jeu d'Échecs en Python

Ce projet est une implémentation complète d'un jeu d'échecs en Python, offrant à la fois une interface web et la possibilité de jouer contre une IA.

## Fonctionnalités

- **Interface Web** : Interface utilisateur intuitive basée sur Flask
- **Modes de jeu multiples** :
  - Humain contre Humain
  - Humain contre IA
  - IA contre IA
- **Niveaux de difficulté de l'IA** : Facile, Moyen, Difficile
- **Sauvegarde et chargement de parties**
- **Visualisation des coups valides**
- **Promotion des pions**
- **Détection automatique des situations spéciales** :
  - Échec
  - Échec et mat
  - Pat (match nul)
- **Historique des coups**
- **Visualisation des "pensées" de l'IA**

## Structure du Projet

```
echec python/
├── app.py                 # Application Flask principale
├── game/                  # Logique du jeu d'échecs
│   ├── ai.py              # Intelligence artificielle
│   ├── board.py           # Plateau de jeu
│   ├── game.py            # Gestion de la partie
│   ├── game_manager.py    # Gestion des parties multiples
│   ├── game_state.py      # État du jeu
│   ├── history.py         # Historique des coups
│   ├── move.py            # Logique des mouvements
│   ├── pieces/            # Classes des pièces d'échecs
│   │   ├── bishop.py      # Fou
│   │   ├── king.py        # Roi
│   │   ├── knight.py      # Cavalier
│   │   ├── pawn.py        # Pion
│   │   ├── piece.py       # Classe de base pour les pièces
│   │   ├── queen.py       # Reine
│   │   └── rook.py        # Tour
│   └── rules/             # Règles du jeu
│       ├── game_rules.py  # Règles générales
│       └── movement_rules.py # Règles de mouvement
├── main.py                # Point d'entrée pour la version console
├── requirements.txt       # Dépendances du projet
├── routes/                # Routes de l'API web
│   └── board_routes.py    # Routes pour le plateau
├── run.py                 # Script pour lancer l'application web
├── saved_games/           # Parties sauvegardées
├── templates/             # Templates HTML pour l'interface web
│   ├── ai_stats.html      # Statistiques de l'IA
│   ├── available_games.html # Liste des parties disponibles
│   ├── board.html         # Affichage du plateau
│   ├── index.html         # Page d'accueil
│   └── saved_games.html   # Liste des parties sauvegardées
├── ui/                    # Interfaces utilisateur
│   ├── gui.py             # Interface graphique
│   └── text_interface.py  # Interface texte
└── utils/                 # Utilitaires
    └── helpers.py         # Fonctions d'aide
```

## Prérequis

- Python 3.6 ou supérieur
- Flask 2.3.2

## Installation

1. Clonez ce dépôt :

   ```
   git clone <URL_du_dépôt>
   cd echec-python
   ```

2. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```

## Utilisation

### Interface Web

1. Lancez l'application web :

   ```
   python run.py
   ```

2. Ouvrez votre navigateur et accédez à :

   ```
   http://localhost:5000
   ```

3. Vous pouvez maintenant :
   - Créer une nouvelle partie
   - Rejoindre une partie existante
   - Jouer contre l'IA
   - Consulter les parties sauvegardées

### Interface Console (optionnelle)

Pour jouer en mode console :

```
python main.py
```

## Fonctionnement de l'IA

L'IA utilise une combinaison de techniques pour déterminer le meilleur coup :

- Algorithme Minimax avec élagage Alpha-Beta
- Évaluation de la position basée sur la valeur des pièces et leur position
- Livre d'ouvertures pour les premiers coups
- Apprentissage à partir des parties précédentes

## Sauvegarde des Parties

Les parties sont automatiquement sauvegardées au format JSON dans le dossier `saved_games/`. Vous pouvez les consulter et les rejouer via l'interface web.

## Tests

Le projet inclut des tests unitaires pour vérifier le bon fonctionnement des composants principaux :

```
python -m unittest discover tests
```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## Licence

Ce projet est sous licence libre.
