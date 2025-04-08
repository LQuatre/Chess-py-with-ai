# queen.py

from game.pieces.piece import Piece
from game.pieces.rook import Rook
from game.pieces.bishop import Bishop

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.rook = Rook(color)
        self.bishop = Bishop(color)

    def __str__(self):
        return "♕" if self.color == "white" else "♛"

    def get_valid_moves(self, row, col, board):
        # La dame combine les mouvements de la tour et du fou
        return self.rook.get_valid_moves(row, col, board) + self.bishop.get_valid_moves(row, col, board)
