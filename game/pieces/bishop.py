# bishop.py

from game.pieces.piece import Piece

class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color)

    def __str__(self):
        return "♗" if self.color == "white" else "♝"

    def get_valid_moves(self, row, col, board):
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonales

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
