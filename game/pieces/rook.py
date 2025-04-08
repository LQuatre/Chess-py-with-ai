# rook.py

from game.pieces.piece import Piece

class Rook(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.has_moved = False  # Pour vérifier si la tour a déjà bougé (important pour le roque)
        self.has_moved = False  # Pour vérifier si la tour a déjà bougé (important pour le roque)

    def __str__(self):
        return "♖" if self.color == "white" else "♜"
    
    def get_color(self):
        return self.color

    def get_valid_moves(self, row, col, board):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Haut, Bas, Gauche, Droite

        for direction in directions:
            r, c = row, col
            while True:
                r += direction[0]
                c += direction[1]
                if 0 <= r < 8 and 0 <= c < 8:
                    if board.get_board()[r][c] == "":  # Case vide
                        moves.append((r, c))
                    elif board.get_board()[r][c].color != self.color:  # Pièce adverse
                        moves.append((r, c))
                        break
                    else:
                        break
                else:
                    break
        return moves
