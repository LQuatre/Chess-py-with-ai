# game_rules.py

class GameRules:
    def __init__(self):
        pass

    def is_check(self, board, color):
        """
        Vérifie si le roi du joueur est en échec.
        """
        return board.is_king_in_check(color)

    def is_checkmate(self, board, color):
        """
        Vérifie si le joueur est en échec et mat.
        """
        # Vérifier si le roi est en échec
        if not board.is_king_in_check(color):
            return False
        
        # Vérifier si le joueur a des mouvements valides
        for row in range(8):
            for col in range(8):
                piece = board.get_board()[row][col]
                if piece != "" and isinstance(piece, object) and hasattr(piece, 'color') and piece.color == color:
                    valid_moves = board.get_valid_moves(row, col)
                    if valid_moves:
                        return False
        
        # Si le roi est en échec et qu'aucun mouvement valide n'est disponible, c'est un échec et mat
        return True

    def is_stalemate(self, board, color):
        """
        Vérifie si la partie est en pat (égalité).
        """
        # Vérifier si le roi n'est pas en échec
        if board.is_king_in_check(color):
            return False
        
        # Vérifier si le joueur a des mouvements valides
        for row in range(8):
            for col in range(8):
                piece = board.get_board()[row][col]
                if piece != "" and isinstance(piece, object) and hasattr(piece, 'color') and piece.color == color:
                    valid_moves = board.get_valid_moves(row, col)
                    if valid_moves:
                        return False
        
        # Si le roi n'est pas en échec et qu'aucun mouvement valide n'est disponible, c'est un pat
        return True
