# game.py

from game.board import Board

class Game:
    def __init__(self):
        self.board = Board()  # Crée un plateau de jeu
        self.turn = "white"   # Le joueur blanc commence
        self.opponent = "black" # Le joueur est l'adversaire du joueur courant
        self.game_over = False
        self.winner = None

    def switch_turn(self):
        """Change de tour entre les joueurs."""
        self.turn = "black" if self.turn == "white" else "white"
        self.opponent = "white" if self.opponent == "black" else "black"

    def play_turn(self, start_pos, end_pos):
        """Effectue un coup pour le joueur courant."""
        start_row, start_col = self.board.chess_notation_to_index(start_pos)
        end_row, end_col = self.board.chess_notation_to_index(end_pos)
        
        piece = self.board.board[start_row][start_col]

        if piece == "":
            return False, "Aucune pièce à cette position"
            
        if piece.color != self.turn:
            return False, "Ce n'est pas votre pièce !"

        # Vérifie si le coup est valide
        valid_moves = self.board.get_valid_moves(start_row, start_col)
        if (end_row, end_col) not in valid_moves:
            return False, "Coup invalide !"
        
        # Déplace la pièce sur l'échiquier
        move_result = self.board.execute_move(start_pos, end_pos)
        if not move_result:
            return False, "Mouvement impossible"
        
        # Synchroniser le tour avec celui du plateau
        self.turn = self.board.turn
        self.opponent = self.board.opponent
        
        # Vérifie l'état du jeu après le coup
        game_status = self.board.check_game_status()
        message = ""
        
        if game_status == "Checkmate":
            self.game_over = True
            self.winner = "white" if self.turn == "black" else "black"
            message = f"Échec et mat ! {self.winner} gagne."
        elif game_status == "Check":
            message = f"Le roi de {self.opponent} est en échec !"
        elif game_status == "Stalemate":
            self.game_over = True
            message = "Pat ! Match nul."
        
        # Vérifier directement si le roi adverse est en échec ou échec et mat
        if self.board.is_king_in_check(self.opponent):
            message = f"Le roi de {self.opponent} est en échec !"
            if self.board.is_checkmate(self.opponent):
                self.game_over = True
                self.winner = self.turn
                message = f"Échec et mat ! {self.winner.capitalize()} gagne."
        
        return True, message

    def get_game_state(self):
        """Retourne l'état actuel du jeu."""
        return {
            "board": self.board.to_list(),
            "turn": self.turn,
            "game_over": self.game_over,
            "winner": self.winner
        }