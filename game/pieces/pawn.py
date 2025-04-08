# pawn.py

from game.pieces.rook import Rook
from game.pieces.knight import Knight
from game.pieces.bishop import Bishop
from game.pieces.queen import Queen
from game.pieces.piece import Piece

class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color)

    def __str__(self):
        return "♙" if self.color == "white" else "♟"

    def get_valid_moves(self, row, col, board):
        moves = []
        direction = -1 if self.color == "white" else 1  # Direction du mouvement : blanc monte, noir descend

        # print("Row: ", row, "Col: ", col)
        # print("Direction: ", direction)
        # print(self.color)

        # Mouvement de base (1 case en avant)
        if 0 <= row + direction < 8 and board.get_board()[row + direction][col] == "":
            # print(board[row + direction][col])
            # print("Case vide")
            # print("Row: ", row + direction, "Col: ", col)
            # print("Direction: ", direction)
            moves.append((row + direction, col))

        # Premier mouvement du pion (2 cases en avant)
        if (self.color == "white" and row == 6) or (self.color == "black" and row == 1):
            if board.get_board()[row + direction][col] == "" and board.get_board()[row + 2 * direction][col] == "":
                moves.append((row + 2 * direction, col))

        # Captures en diagonale
        for diag in [-1, 1]:
            new_col = col + diag
            if 0 <= row + direction < 8 and 0 <= new_col < 8:
                target_piece = board.get_board()[row + direction][new_col]
                if target_piece and target_piece.color != self.color:  # Capture d'une pièce adverse
                    moves.append((row + direction, new_col))

        # Prise en passant
        if hasattr(board, "history") and board.history:
            if hasattr(board.history, "length") and board.history.length() <= 2:
                return moves
            if hasattr(board.history, "get_last_move"):
                last_move = board.history.get_last_move()
                if not isinstance(last_move.get("Piece"), Pawn):
                    return moves
                start_row, start_col = last_move["start"]
                end_row, end_col = last_move["end"]
                last_piece = board.get_board()[end_row][end_col]
                if isinstance(last_piece, Pawn) and last_piece.color != self.color:
                    if (self.color == "black" and end_row == 4) or (self.color == "white" and end_row == 3):
                        if abs(end_col - col) == 1:
                            moves.append((row + direction, end_col))
                            print(f"Prise en passant possible à ({row + direction}, {end_col})")

        return moves
    
