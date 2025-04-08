# game_state.py
from game.board import Board
from game.game import Game

# Singleton pour stocker l'état du jeu
class GameState:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GameState()
        return cls._instance
    
    def __init__(self):
        self.game = Game()
        self.board = self.game.board
    
    def reset_game(self):
        self.game = Game()
        self.board = self.game.board