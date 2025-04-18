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
        is_check, attacker_pos, attacker_piece = board.is_king_in_check(color, return_attacker=True)
        if not is_check:
            return False
        
        # Trouver la position du roi
        king_position = board.find_king(color)
        if not king_position:
            return False  # Pas de roi, pas d'échec et mat
        
        # Vérifier si le roi peut se déplacer pour échapper à l'échec
        king_row, king_col = king_position
        king_piece = board.get_board()[king_row][king_col]
        king_valid_moves = board.get_valid_moves(king_row, king_col)
        
        # Si le roi peut se déplacer, ce n'est pas un échec et mat
        if king_valid_moves:
            # Vérifier si ces mouvements permettent d'échapper à l'échec
            for move_row, move_col in king_valid_moves:
                # Simuler le mouvement
                temp_board = board.copy()
                temp_board.board[move_row][move_col] = king_piece
                temp_board.board[king_row][king_col] = ""
                
                # Vérifier si le roi est toujours en échec après ce mouvement
                if not temp_board.is_king_in_check(color):
                    return False  # Le roi peut échapper à l'échec
        
        # Vérifier si une pièce peut capturer l'attaquant
        if attacker_pos:
            attacker_row, attacker_col = attacker_pos
            for row in range(8):
                for col in range(8):
                    piece = board.get_board()[row][col]
                    if piece != "" and hasattr(piece, 'color') and piece.color == color:
                        # Ne pas considérer le roi lui-même (déjà vérifié)
                        if (row, col) == king_position:
                            continue
                        
                        # Vérifier si la pièce peut capturer l'attaquant
                        valid_moves = board.get_valid_moves(row, col)
                        for move_row, move_col in valid_moves:
                            if (move_row, move_col) == attacker_pos:
                                # Simuler la capture
                                temp_board = board.copy()
                                temp_board.board[move_row][move_col] = piece
                                temp_board.board[row][col] = ""
                                
                                # Vérifier si le roi est toujours en échec après cette capture
                                if not temp_board.is_king_in_check(color):
                                    return False  # Une pièce peut capturer l'attaquant
        
        # Si l'attaquant est un cavalier, on ne peut pas s'interposer
        if attacker_piece and hasattr(attacker_piece, '__class__') and attacker_piece.__class__.__name__ == 'Knight':
            # Si on ne peut ni déplacer le roi ni capturer le cavalier, c'est échec et mat
            return True
        
        # Vérifier si une pièce peut s'interposer entre le roi et l'attaquant
        # (seulement pour les attaques en ligne ou en diagonale)
        if attacker_pos and king_position:
            # Obtenir le chemin entre l'attaquant et le roi
            path = board.get_path_between(attacker_pos, king_position)
            
            # Vérifier si une pièce amie peut se déplacer sur ce chemin
            for row in range(8):
                for col in range(8):
                    piece = board.get_board()[row][col]
                    if piece != "" and hasattr(piece, 'color') and piece.color == color:
                        # Ne pas considérer le roi lui-même
                        if (row, col) == king_position:
                            continue
                        
                        # Vérifier si la pièce peut se déplacer sur une case du chemin
                        valid_moves = board.get_valid_moves(row, col)
                        for move_row, move_col in valid_moves:
                            if (move_row, move_col) in path:
                                # Simuler l'interposition
                                temp_board = board.copy()
                                temp_board.board[move_row][move_col] = piece
                                temp_board.board[row][col] = ""
                                
                                # Vérifier si le roi est toujours en échec après cette interposition
                                if not temp_board.is_king_in_check(color):
                                    return False  # Une pièce peut s'interposer
        
        # Si le roi est en échec et qu'aucune solution n'est disponible, c'est un échec et mat
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
