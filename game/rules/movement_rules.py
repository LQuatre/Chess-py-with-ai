# movement_rules.py

from game.pieces.pawn import Pawn
from game.pieces.rook import Rook
from game.pieces.knight import Knight
from game.pieces.bishop import Bishop
from game.pieces.queen import Queen
from game.pieces.king import King

class MovementRules:
    def __init__(self):
        self.piece_rules = {
            "pawn": Pawn,
            "rook": Rook,
            "knight": Knight,
            "bishop": Bishop,
            "queen": Queen,
            "king": King,
        }

    def get_valid_moves(self, piece, row, col, board):
        """
        Renvoie les coups valides pour une pièce donnée selon sa classe.
        """
        piece_class = self.piece_rules.get(piece.__class__.__name__.lower())
        if piece_class:
            return piece_class(piece.color).get_valid_moves(row, col, board)
        return []
