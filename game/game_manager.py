# game_manager.py
import uuid
from game.game import Game

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
    
    def create_game(self):
        """Crée une nouvelle partie et retourne son ID."""
        game_id = str(uuid.uuid4())
        self.games[game_id] = Game()
        self.game_players[game_id] = [None, None]  # [white_player, black_player]
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
        
        if players[0] is None:  # Joueur blanc disponible
            players[0] = player_id
            self.player_games[player_id] = game_id
            return True, "Vous jouez les blancs"
        elif players[1] is None:  # Joueur noir disponible
            players[1] = player_id
            self.player_games[player_id] = game_id
            return True, "Vous jouez les noirs"
        else:
            return False, "La partie est complète"
    
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
        return player_color == game.turn
    
    def list_available_games(self):
        """Liste les parties disponibles pour rejoindre."""
        available_games = []
        for game_id, players in self.game_players.items():
            if None in players and not self.games[game_id].game_over:
                available_games.append({
                    "id": game_id,
                    "white_player": players[0] is not None,
                    "black_player": players[1] is not None
                })
        return available_games# game_manager.py
import uuid
from game.game import Game

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
    
    def create_game(self):
        """Crée une nouvelle partie et retourne son ID."""
        game_id = str(uuid.uuid4())
        self.games[game_id] = Game()
        self.game_players[game_id] = [None, None]  # [white_player, black_player]
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
        
        if players[0] is None:  # Joueur blanc disponible
            players[0] = player_id
            self.player_games[player_id] = game_id
            return True, "Vous jouez les blancs"
        elif players[1] is None:  # Joueur noir disponible
            players[1] = player_id
            self.player_games[player_id] = game_id
            return True, "Vous jouez les noirs"
        else:
            return False, "La partie est complète"
    
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
        return player_color == game.turn
    
    def list_available_games(self):
        """Liste les parties disponibles pour rejoindre."""
        available_games = []
        for game_id, players in self.game_players.items():
            if None in players and not self.games[game_id].game_over:
                available_games.append({
                    "id": game_id,
                    "white_player": players[0] is not None,
                    "black_player": players[1] is not None
                })
        return available_games