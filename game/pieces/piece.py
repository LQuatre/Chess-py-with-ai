# piece.py

class Piece:
    def __init__(self, color):
        self.color = color  # "white" ou "black"

    def __str__(self):
        """
        Méthode spéciale pour afficher la pièce.
        """
        raise NotImplementedError("Cette méthode doit être implémentée dans chaque pièce spécifique.")
    
    def get_color(self):
        """
        Renvoie la couleur de la pièce.
        """
        return self.color

    def get_valid_moves(self, row, col, board):
        """
        Méthode à implémenter dans chaque sous-classe pour obtenir les coups possibles d'une pièce spécifique.
        """
        raise NotImplementedError("Cette méthode doit être implémentée dans chaque pièce spécifique.")
