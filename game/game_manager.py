# game_manager.py
import uuid
from game.game import Game

import os
import json
import pickle
from datetime import datetime

class GameManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GameManager()
        return cls._instance
    
    def __init__(self):
        self.games = {}  # Dictionnaire pour stocker les parties {game_id: Game}
        self.player_games = {}  # Dictionnaire pour associer les joueurs aux parties {player_id: game_id}
        self.game_players = {}  # Dictionnaire pour associer les parties aux joueurs {game_id: [white_player_id, black_player_id]}
        
        # Essayer de charger les parties sauvegardées
        self.load_games()
        
    def save_games(self):
        """Sauvegarde toutes les parties actives sur le disque."""
        try:
            # Créer le dossier de sauvegarde s'il n'existe pas
            save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_games')
            os.makedirs(save_dir, exist_ok=True)
            
            # Sauvegarder les parties
            save_path = os.path.join(save_dir, 'active_games.pickle')
            with open(save_path, 'wb') as f:
                pickle.dump(self.games, f)
                
            # Sauvegarder les associations joueurs-parties
            player_save_path = os.path.join(save_dir, 'player_games.json')
            with open(player_save_path, 'w') as f:
                json.dump({
                    'player_games': self.player_games,
                    'game_players': self.game_players
                }, f)
                
            print(f"Parties sauvegardées: {len(self.games)}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des parties: {e}")
            return False
            
    def load_games(self):
        """Charge les parties sauvegardées depuis le disque."""
        try:
            save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_games')
            save_path = os.path.join(save_dir, 'active_games.pickle')
            player_save_path = os.path.join(save_dir, 'player_games.json')
            
            # Vérifier si les fichiers existent
            if os.path.exists(save_path) and os.path.exists(player_save_path):
                # Charger les parties
                with open(save_path, 'rb') as f:
                    self.games = pickle.load(f)
                    
                # Charger les associations joueurs-parties
                with open(player_save_path, 'r') as f:
                    data = json.load(f)
                    self.player_games = data.get('player_games', {})
                    self.game_players = data.get('game_players', {})
                    
                print(f"Parties chargées: {len(self.games)}")
                return True
            return False
        except Exception as e:
            print(f"Erreur lors du chargement des parties: {e}")
            self.games = {}
            self.player_games = {}
            self.game_players = {}
            return False
    
    def create_game(self, white_player_type="human", black_player_type="human", ai_difficulty="medium"):
        """Crée une nouvelle partie et retourne son ID."""
        game_id = str(uuid.uuid4())
        self.games[game_id] = Game(white_player_type, black_player_type, ai_difficulty)
        self.game_players[game_id] = [None, None]  # [white_player, black_player]
        
        # Sauvegarder les parties après chaque création
        self.save_games()
        
        return game_id
    
    def join_game(self, game_id, player_id):
        """Ajoute un joueur à une partie existante."""
        if game_id not in self.games:
            return False, "Partie introuvable"
        
        # Vérifier si le joueur est déjà dans une partie
        if player_id in self.player_games:
            old_game_id = self.player_games[player_id]
            if old_game_id == game_id:
                return True, "Vous êtes déjà dans cette partie"
            
            # Retirer le joueur de son ancienne partie
            self._remove_player_from_game(player_id, old_game_id)
        
        # Ajouter le joueur à la nouvelle partie
        players = self.game_players[game_id]
        game = self.games[game_id]
        
        # Vérifier si les places sont occupées par des IA
        if players[0] is None and game.white_player_type == "human":  # Joueur blanc disponible
            players[0] = player_id
            self.player_games[player_id] = game_id
            
            # Sauvegarder les parties après chaque modification
            self.save_games()
            
            return True, "Vous jouez les blancs"
        elif players[1] is None and game.black_player_type == "human":  # Joueur noir disponible
            players[1] = player_id
            self.player_games[player_id] = game_id
            
            # Sauvegarder les parties après chaque modification
            self.save_games()
            
            return True, "Vous jouez les noirs"
        else:
            return False, "La partie est complète ou les places sont occupées par des IA"
    
    def _remove_player_from_game(self, player_id, game_id):
        """Retire un joueur d'une partie."""
        if game_id in self.game_players:
            players = self.game_players[game_id]
            if players[0] == player_id:
                players[0] = None
            elif players[1] == player_id:
                players[1] = None
        
        if player_id in self.player_games:
            del self.player_games[player_id]
    
    def get_game(self, game_id):
        """Retourne une partie par son ID."""
        return self.games.get(game_id)
    
    def get_player_game(self, player_id):
        """Retourne l'ID de la partie d'un joueur."""
        return self.player_games.get(player_id)
    
    def get_player_color(self, game_id, player_id):
        """Retourne la couleur d'un joueur dans une partie."""
        if game_id not in self.game_players:
            return None
        
        players = self.game_players[game_id]
        if players[0] == player_id:
            return "white"
        elif players[1] == player_id:
            return "black"
        return None
    
    def is_player_turn(self, game_id, player_id):
        """Vérifie si c'est le tour du joueur."""
        game = self.get_game(game_id)
        if not game:
            return False
        
        player_color = self.get_player_color(game_id, player_id)
        if not player_color:
            return False
            
        # Si c'est le tour d'une IA, ce n'est pas le tour du joueur
        if (player_color == "white" and game.white_player_type == "ai") or \
           (player_color == "black" and game.black_player_type == "ai"):
            return False
            
        return player_color == game.turn
    
    def list_available_games(self):
        """Liste les parties disponibles pour rejoindre."""
        available_games = []
        for game_id, players in self.game_players.items():
            game = self.games[game_id]
            if not game.game_over:
                # Vérifier si des places pour humains sont disponibles
                white_available = players[0] is None and game.white_player_type == "human"
                black_available = players[1] is None and game.black_player_type == "human"
                
                if white_available or black_available:
                    available_games.append({
                        "id": game_id,
                        "white_player": not white_available,  # True si occupé
                        "black_player": not black_available,  # True si occupé
                        "white_player_type": game.white_player_type,
                        "black_player_type": game.black_player_type
                    })
        return available_games
        
    def set_player_type(self, game_id, color, player_type, ai_difficulty="medium"):
        """Change le type de joueur (humain ou IA) pour une partie."""
        game = self.get_game(game_id)
        if not game:
            return False, "Partie introuvable"
            
        # Changer le type de joueur
        success, message = game.set_player_type(color, player_type, ai_difficulty)
        
        # Mettre à jour les joueurs si nécessaire
        if success and player_type == "ai":
            players = self.game_players[game_id]
            if color == "white" and players[0] is not None:
                # Retirer le joueur humain
                player_id = players[0]
                players[0] = None
                if player_id in self.player_games:
                    del self.player_games[player_id]
            elif color == "black" and players[1] is not None:
                # Retirer le joueur humain
                player_id = players[1]
                players[1] = None
                if player_id in self.player_games:
                    del self.player_games[player_id]
                    
        return success, message
        
    def create_ai_vs_ai_game(self, white_difficulty="medium", black_difficulty="medium"):
        """Crée une partie IA contre IA."""
        return self.create_game("ai", "ai", white_difficulty if white_difficulty == black_difficulty else "custom")
        
    def create_human_vs_ai_game(self, human_color="white", ai_difficulty="medium"):
        """Crée une partie Humain contre IA."""
        if human_color == "white":
            return self.create_game("human", "ai", ai_difficulty)
        else:
            return self.create_game("ai", "human", ai_difficulty)