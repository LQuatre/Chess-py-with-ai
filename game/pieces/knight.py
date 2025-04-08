# knight.py

from game.pieces.piece import Piece

class Knight(Piece):
    def __init__(self, color):
        super().__init__(color)
        
    def __str__(self):
        return "♘" if self.color == "white" else "♞"

    def get_valid_moves(self, row, col, board):
        moves = []
        directions = [
            (-2, -1), (-2, 1), (2, -1), (2, 1),
            (-1, -2), (-1, 2), (1, -2), (1, 2)
        ]

        for direction in directions:
            r, c = row + direction[0], col + direction[1]
            if 0 <= r < 8 and 0 <= c < 8:
                if board.get_board()[r][c] == "" or board.get_board()[r][c].color != self.color:  # Case vide ou pièce adverse
                    moves.append((r, c))

        return moves
