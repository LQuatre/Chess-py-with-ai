# board.py

from game.pieces.rook import Rook
from game.pieces.knight import Knight
from game.pieces.bishop import Bishop
from game.pieces.queen import Queen
from game.pieces.king import King
from game.pieces.pawn import Pawn
from game.rules.movement_rules import MovementRules
from game.rules.game_rules import GameRules
import pandas as pd
from game.move import Move
from game.history import GameHistory

class Board:
    def __init__(self):
        # Initialisation du plateau avec les pièces appropriées
        self.board = [
            [Rook("black"), Knight("black"), Bishop("black"), Queen("black"), King("black"), Bishop("black"), Knight("black"), Rook("black")],
            [Pawn("black")]*8,
            [""]*8,
            [""]*8,
            [""]*8,
            [""]*8,
            [Pawn("white")]*8,
            [Rook("white"), Knight("white"), Bishop("white"), Queen("white"), King("white"), Bishop("white"), Knight("white"), Rook("white")]
        ]
        self.movement_rules = MovementRules()
        self.game_rules = GameRules()
        self.turn = "white"
        self.opponent = "black"
        self.history = GameHistory()
        self.move_count = 1
        self.promotion_pending = None  # Pour stocker les informations sur un pion en attente de promotion

    def get_board(self):
        """Retourne la pièce à la position (row, col)"""
        return self.board
    
    def set_board(self, board):
        """Place une pièce à la position (row, col)"""
        self.board = board
    
    def get_piece(self, row, col):
        """Retourne la pièce à la position (row, col)"""
        return self.board[row][col]
    
    def set_piece(self, row, col, piece):
        """Place une pièce à la position (row, col)"""
        self.board[row][col] = piece
    
    def get(self):
        return self
    
    def get_turn(self):
        return self.turn
    
    def copy(self):
        """Crée une copie du plateau."""
        new_board = Board()
        new_board.set_board([row.copy() for row in self.board])
        new_board.turn = self.turn
        new_board.opponent = self.opponent
        new_board.move_count = self.move_count
        return new_board

    def get_valid_moves(self, row, col):
        piece = self.board[row][col]
        if piece == "" or piece == " ":
            return []
        return self.movement_rules.get_valid_moves(piece, row, col, self)

    def check_game_status(self):
        if self.game_rules.is_checkmate(self, self.turn):
            return "Checkmate"
        elif self.game_rules.is_check(self, self.turn):
            return "Check"
        elif self.game_rules.is_stalemate(self, self.turn):
            return "Stalemate"
        return "In Progress"
    
    def chess_notation_to_index(self, notation):
        if isinstance(notation, Move):
            notation = notation.to_chess_notation()
        notation = str(notation)  # Ensure notation is a string
        col = ord(notation[0].lower()) - ord('a')
        row = 8 - int(notation[1])
        return row, col

    def execute_move(self, start, end):
        start_row, start_col = self.chess_notation_to_index(start)
        end_row, end_col = self.chess_notation_to_index(end)
        piece = self.board[start_row][start_col]
        valid_moves = self.get_valid_moves(start_row, start_col)
        
        if piece == "" or (end_row, end_col) not in valid_moves:
            print("Invalid move")
            return False

        # Marquer la pièce comme ayant bougé
        if isinstance(piece, King) or isinstance(piece, Rook):
            piece.has_moved = True

        # Handle castling (roque)
        if isinstance(piece, King) and abs(start_col - end_col) == 2:
            # Petit roque (kingside)
            if end_col == 6:
                rook = self.board[start_row][7]
                self.board[start_row][5] = rook  # Déplacer la tour
                self.board[start_row][7] = ""    # Vider la case de la tour
                if isinstance(rook, Rook):
                    rook.has_moved = True
            # Grand roque (queenside)
            elif end_col == 2:
                rook = self.board[start_row][0]
                self.board[start_row][3] = rook  # Déplacer la tour
                self.board[start_row][0] = ""    # Vider la case de la tour
                if isinstance(rook, Rook):
                    rook.has_moved = True

        # Handle en passant capture
        if isinstance(piece, Pawn) and abs(start_col - end_col) == 1 and self.board[end_row][end_col] == "":
            if piece.color == "white" and start_row == 3 and end_row == 2:
                self.board[start_row][end_col] = ""  # Remove the captured pawn
            elif piece.color == "black" and start_row == 4 and end_row == 5:
                self.board[start_row][end_col] = ""  # Remove the captured pawn

        # Déplacer la pièce
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = ""

        # Vérifier si le roi est en échec après le mouvement
        if self.is_king_in_check(self.turn):
            print("Move puts king in check")
            # Annuler le mouvement
            self.board[start_row][start_col] = piece
            self.board[end_row][end_col] = ""
            
            # Annuler le roque si c'était un roque
            if isinstance(piece, King) and abs(start_col - end_col) == 2:
                if end_col == 6:  # Petit roque
                    rook = self.board[start_row][5]
                    self.board[start_row][7] = rook
                    self.board[start_row][5] = ""
                elif end_col == 2:  # Grand roque
                    rook = self.board[start_row][3]
                    self.board[start_row][0] = rook
                    self.board[start_row][3] = ""
            
            return False

        # Gérer la promotion des pions
        if isinstance(piece, Pawn):
            if (piece.color == "white" and end_row == 0) or (piece.color == "black" and end_row == 7):
                # La promotion sera gérée par une requête séparée
                # On stocke temporairement l'information qu'un pion doit être promu
                self.promotion_pending = {
                    "row": end_row,
                    "col": end_col,
                    "color": piece.color
                }

        # Préparer le message pour l'historique
        move_message = f"{piece} moved from {start} to {end}"
        
        # Changer de tour
        next_turn = "black" if self.turn == "white" else "white"
        next_opponent = "white" if next_turn == "black" else "black"
        
        # Vérifier si le roi adverse est en échec ou échec et mat
        if self.is_king_in_check(next_turn):
            if self.is_checkmate(next_turn):
                move_message += f" - ÉCHEC ET MAT ! {self.turn.capitalize()} gagne."
            else:
                move_message += f" - ÉCHEC au roi {next_turn} !"
        
        # Add move to history
        self.history.add_move(
            self.move_count,
            self.turn.capitalize(),
            (start_row, start_col),
            (end_row, end_col),
            piece,
            move_message
        )
        if self.turn == "black":
            self.move_count += 1

        # Mettre à jour le tour
        self.turn = next_turn
        self.opponent = next_opponent
        self.history.display_history()
        return True
    
    def display(self):
        display_board = [[str(piece) if piece != "" else "" for piece in row] for row in self.board]
        df = pd.DataFrame(display_board, index=range(8, 0, -1), columns=list("abcdefgh"))
        print(df)

    def get_display_board(self):
        """Retourne le plateau sous forme de DataFrame pour l'affichage."""
        display_board = [[str(piece) if piece != "" else "" for piece in row] for row in self.board]
        df = pd.DataFrame(display_board, index=range(8, 0, -1), columns=list("abcdefgh"))
        return df

    def is_king_in_check(self, color):
        """Vérifie si le roi de la couleur donnée est en échec."""
        if not color:
            print("aucune couleur valid")
            return False
        king_position = self.find_king(color)
        if not king_position:
            return False
        return self.is_square_attacked(king_position, color)

    def find_king(self, color):
        """Trouve la position du roi de la couleur donnée."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece == "":  # Case vide
                    continue
                if isinstance(piece, King) and piece.color == color:
                    return (row, col)
        return None

    def is_square_attacked(self, position, color):
        """Vérifie si une case est attaquée par une pièce de l'adversaire."""
        opponent_color = "white" if color == "black" else "black"
        target_row, target_col = position
        
        # Vérifier les attaques des pions
        pawn_directions = [(-1, -1), (-1, 1)] if color == "white" else [(1, -1), (1, 1)]
        for d_row, d_col in pawn_directions:
            r, c = target_row + d_row, target_col + d_col
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != "" and piece.color == opponent_color and isinstance(piece, Pawn):
                    return True
        
        # Vérifier les attaques des cavaliers
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for d_row, d_col in knight_moves:
            r, c = target_row + d_row, target_col + d_col
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != "" and piece.color == opponent_color and isinstance(piece, Knight):
                    return True
        
        # Vérifier les attaques en ligne (tour et dame)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for d_row, d_col in directions:
            r, c = target_row, target_col
            while True:
                r += d_row
                c += d_col
                if not (0 <= r < 8 and 0 <= c < 8):
                    break
                piece = self.board[r][c]
                if piece == "":
                    continue
                if piece.color == opponent_color and (isinstance(piece, Rook) or isinstance(piece, Queen)):
                    return True
                break  # Une pièce bloque la ligne
        
        # Vérifier les attaques en diagonale (fou et dame)
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for d_row, d_col in directions:
            r, c = target_row, target_col
            while True:
                r += d_row
                c += d_col
                if not (0 <= r < 8 and 0 <= c < 8):
                    break
                piece = self.board[r][c]
                if piece == "":
                    continue
                if piece.color == opponent_color and (isinstance(piece, Bishop) or isinstance(piece, Queen)):
                    return True
                break  # Une pièce bloque la diagonale
        
        # Vérifier les attaques du roi
        king_moves = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for d_row, d_col in king_moves:
            r, c = target_row + d_row, target_col + d_col
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != "" and piece.color == opponent_color and isinstance(piece, King):
                    return True
        
        return False
    
    def is_king_surrounded(self, color):
        """Vérifie si le roi de la couleur donnée est entouré par des pièces adverses et que ces cases ne sont pas attaquées."""
        king_position = self.find_king(color)
        if not king_position:
            return False
            
        row, col = king_position
        directions = [
            (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)
        ]
        for direction in directions:
            r, c = row + direction[0], col + direction[1]
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece == "" or piece.color != color:
                    if not self.is_square_attacked((r, c), color):
                        print(f"Le roi n'est pas entouré par des pièces adverses en ({r}, {c}).")
                        return False
        return True

    def is_checkmate(self, color):
        """Vérifie si le roi de la couleur donnée est en échec et mat."""
        return self.game_rules.is_checkmate(self, color)
    def is_promoted(self, row, col):
        """Vérifie si un pion a atteint la dernière rangée."""
        piece = self.board[row][col]
        if isinstance(piece, Pawn):
            print(f"Piece: {piece}, Row: {row}, Col: {col}")
            if (piece.color == "white" and row == 0) or (piece.color == "black" and row == 7):
                return True
        return False
    
    def promote_pawn(self, row, col, piece_type):
        """Promouvoir un pion en une autre pièce.
        
        Args:
            row: La ligne du pion à promouvoir
            col: La colonne du pion à promouvoir
            piece_type: Le type de pièce en lequel promouvoir ('Q', 'R', 'B', 'N')
        
        Returns:
            bool: True si la promotion a réussi, False sinon
        """
        piece = self.board[row][col]
        
        if not isinstance(piece, Pawn):
            return False
            
        color = piece.color
        
        # Vérifier si le pion est en position de promotion
        if not ((color == "white" and row == 0) or (color == "black" and row == 7)):
            return False
            
        switcher = {
            "Q": Queen,
            "R": Rook,
            "B": Bishop,
            "N": Knight
        }
        
        if piece_type in switcher:
            self.board[row][col] = switcher[piece_type](color)
            self.promotion_pending = None
            return True
            
        return False
        
    def has_promotion_pending(self):
        """Vérifie s'il y a un pion en attente de promotion."""
        return self.promotion_pending is not None
        
    def get_promotion_info(self):
        """Retourne les informations sur le pion en attente de promotion."""
        return self.promotion_pending
    
    def to_dict(self):
        """Convertit le plateau en un dictionnaire pour l'API."""
        board_dict = {
            "board": [
                [str(piece) if piece != "" else "" for piece in row] for row in self.board
            ],
            "turn": self.turn,
            "opponent": self.opponent,
            "move_count": self.move_count,
            "history": self.history.moves.to_dict(orient='records')
        }
        return board_dict
    
    def to_list(self):
        """Convertit le plateau en une liste 2D de chaînes pour l'affichage."""
        return [[str(piece) if piece != "" else "" for piece in row] for row in self.board]