# king.py

from game.pieces.piece import Piece

class King(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.has_moved = False  # Pour vérifier si le roi a déjà bougé (important pour le roque)

    def __str__(self):
        return "♔" if self.color == "white" else "♚"

    def get_valid_moves(self, row, col, board):
        moves = []
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        # Utiliser directement le plateau pour vérifier les mouvements possibles
        for direction in directions:
            r, c = row + direction[0], col + direction[1]
            if 0 <= r < 8 and 0 <= c < 8:
                # Vérifier si la case est vide ou contient une pièce adverse
                target_piece = board.get_board()[r][c]
                if target_piece == "" or (isinstance(target_piece, Piece) and target_piece.color != self.color):
                    # Simuler le mouvement pour vérifier si le roi ne se met pas en échec
                    simulate_board = board.copy()
                    simulate_board.set_piece(row, col, "")  # Enlève le roi de sa position actuelle
                    simulate_board.set_piece(r, c, self)    # Place le roi à la nouvelle position
                    
                    # Vérifier si le roi n'est pas en échec après ce mouvement
                    if not simulate_board.is_king_in_check(self.color):
                        moves.append((r, c))
        
        # Vérifier les possibilités de roque
        castling_moves = self.get_castling_moves(row, col, board)
        moves.extend(castling_moves)

        return moves
    
    def get_castling_moves(self, row, col, board):
        """Vérifie si le roque est possible et retourne les mouvements valides."""
        castling_moves = []
        
        # Si le roi a déjà bougé, le roque n'est pas possible
        if self.has_moved:
            return []
        
        # Vérifier si le roi est en échec
        if board.is_king_in_check(self.color):
            return []
        
        # Positions initiales du roi
        king_row = 7 if self.color == "white" else 0
        
        # Vérifier si le roi est à sa position initiale
        if row != king_row or col != 4:
            return []
        
        # Vérifier le petit roque (côté roi)
        if self.can_castle_kingside(board, king_row):
            castling_moves.append((king_row, 6))  # Position du roi après le petit roque
        
        # Vérifier le grand roque (côté reine)
        if self.can_castle_queenside(board, king_row):
            castling_moves.append((king_row, 2))  # Position du roi après le grand roque
        
        return castling_moves
    
    def can_castle_kingside(self, board, king_row):
        """Vérifie si le petit roque est possible."""
        # Vérifier si la tour est à sa place et n'a pas bougé
        rook_col = 7
        rook = board.get_board()[king_row][rook_col]
        
        if not rook or not isinstance(rook, Piece) or rook.__class__.__name__ != "Rook" or rook.color != self.color:
            return False
        
        # Vérifier si la tour a déjà bougé
        if hasattr(rook, "has_moved") and rook.has_moved:
            return False
        
        # Vérifier si les cases entre le roi et la tour sont vides
        for col in range(5, 7):
            if board.get_board()[king_row][col] != "":
                return False
        
        # Vérifier si le roi ne passe pas par une case attaquée
        for col in range(4, 7):
            if board.is_square_attacked((king_row, col), self.color):
                return False
        
        return True
    
    def can_castle_queenside(self, board, king_row):
        """Vérifie si le grand roque est possible."""
        # Vérifier si la tour est à sa place et n'a pas bougé
        rook_col = 0
        rook = board.get_board()[king_row][rook_col]
        
        if not rook or not isinstance(rook, Piece) or rook.__class__.__name__ != "Rook" or rook.color != self.color:
            return False
        
        # Vérifier si la tour a déjà bougé
        if hasattr(rook, "has_moved") and rook.has_moved:
            return False
        
        # Vérifier si les cases entre le roi et la tour sont vides
        for col in range(1, 4):
            if board.get_board()[king_row][col] != "":
                return False
        
        # Vérifier si le roi ne passe pas par une case attaquée
        for col in range(2, 5):
            if board.is_square_attacked((king_row, col), self.color):
                return False
        
        return True
