# game.py

from game.board import Board
from game.ai import AI

class Game:
    def __init__(self, white_player_type="human", black_player_type="human", ai_difficulty="medium"):
        self.board = Board()  # Crée un plateau de jeu
        self.turn = "white"   # Le joueur blanc commence
        self.opponent = "black" # Le joueur est l'adversaire du joueur courant
        self.game_over = False
        self.winner = None
        
        # Configuration des joueurs (human ou ai)
        self.white_player_type = white_player_type
        self.black_player_type = black_player_type
        
        # Initialisation des IA si nécessaire
        self.white_ai = None
        self.black_ai = None
        
        if white_player_type == "ai":
            self.white_ai = AI(color="white", difficulty=ai_difficulty)
        
        if black_player_type == "ai":
            self.black_ai = AI(color="black", difficulty=ai_difficulty)
        
        # Si c'est le tour de l'IA au début, jouer automatiquement
        if self.turn == "white" and self.white_player_type == "ai":
            self.play_ai_turn()
        elif self.turn == "black" and self.black_player_type == "ai":
            self.play_ai_turn()

    def switch_turn(self):
        """Change de tour entre les joueurs."""
        self.turn = "black" if self.turn == "white" else "white"
        self.opponent = "white" if self.opponent == "black" else "black"

    def play_turn(self, start_pos, end_pos):
        """Effectue un coup pour le joueur courant."""
        try:
            print(f"Traitement du coup: {start_pos} → {end_pos} (tour: {self.turn})")
            
            start_row, start_col = self.board.chess_notation_to_index(start_pos)
            end_row, end_col = self.board.chess_notation_to_index(end_pos)
            
            print(f"Indices convertis: ({start_row}, {start_col}) → ({end_row}, {end_col})")
            
            piece = self.board.board[start_row][start_col]

            if piece == "":
                print(f"Erreur: Aucune pièce à la position {start_pos}")
                return False, "Aucune pièce à cette position"
                
            if piece.color != self.turn:
                print(f"Erreur: Ce n'est pas le tour de {piece.color}, c'est le tour de {self.turn}")
                return False, "Ce n'est pas votre pièce !"

            # Vérifie si le coup est valide
            valid_moves = self.board.get_valid_moves(start_row, start_col)
            print(f"Mouvements valides pour {piece.__class__.__name__} en {start_pos}: {valid_moves}")
            
            if (end_row, end_col) not in valid_moves:
                print(f"Erreur: Coup invalide! ({end_row}, {end_col}) n'est pas dans {valid_moves}")
                return False, "Coup invalide !"
            
            # Déplace la pièce sur l'échiquier
            print(f"Exécution du mouvement sur le plateau")
            move_result = self.board.execute_move(start_pos, end_pos)
            if not move_result:
                print(f"Erreur: Mouvement impossible")
                return False, "Mouvement impossible"
            
            # Synchroniser le tour avec celui du plateau
            self.turn = self.board.turn
            self.opponent = self.board.opponent
            print(f"Tour changé: {self.turn}, Adversaire: {self.opponent}")
            
            # Vérifie l'état du jeu après le coup
            game_status = self.board.check_game_status()
            message = ""
            print(f"État du jeu après le coup: {game_status}")
            
            if game_status == "Checkmate":
                self.game_over = True
                self.winner = "white" if self.turn == "black" else "black"
                message = f"Échec et mat ! {self.winner} gagne."
                print(f"Échec et mat détecté! Gagnant: {self.winner}")
                
                # Apprentissage pour les IA
                self.learn_from_game()
                
            elif game_status == "Check":
                message = f"Le roi de {self.opponent} est en échec !"
                print(f"Échec détecté pour {self.opponent}")
            elif game_status == "Stalemate":
                self.game_over = True
                message = "Pat ! Match nul."
                print("Pat détecté! Match nul.")
                
                # Apprentissage pour les IA en cas de match nul
                self.learn_from_game()
            
            # Vérifier directement si le roi adverse est en échec ou échec et mat
            if self.board.is_king_in_check(self.opponent):
                message = f"Le roi de {self.opponent} est en échec !"
                print(f"Vérification supplémentaire: Le roi de {self.opponent} est en échec")
                
                if self.board.is_checkmate(self.opponent):
                    self.game_over = True
                    self.winner = self.turn
                    message = f"Échec et mat ! {self.winner.capitalize()} gagne."
                    print(f"Vérification supplémentaire: Échec et mat! Gagnant: {self.winner}")
                    
                    # Apprentissage pour les IA
                    self.learn_from_game()
            
            # Si c'est maintenant le tour de l'IA, jouer automatiquement
            if not self.game_over:
                if (self.turn == "white" and self.white_player_type == "ai") or \
                   (self.turn == "black" and self.black_player_type == "ai"):
                    print(f"C'est le tour de l'IA ({self.turn}), joue automatiquement")
                    ai_success, ai_message = self.play_ai_turn()
                    if ai_success:
                        message += f" {ai_message}"
                        print(f"Coup de l'IA réussi: {ai_message}")
                    else:
                        print(f"Erreur lors du coup de l'IA: {ai_message}")
            
            # Sauvegarder la partie
            print("Sauvegarde de l'état de la partie")
            self.save_game_state()
            
            print(f"Coup terminé avec succès: {message}")
            return True, message
            
        except Exception as e:
            import traceback
            print(f"Erreur lors du traitement du coup: {str(e)}")
            print(traceback.format_exc())
            return False, f"Erreur interne: {str(e)}"
        
    def learn_from_game(self):
        """Fait apprendre aux IA à partir du résultat de la partie."""
        if self.white_ai and self.black_ai:
            # Déterminer le résultat pour chaque IA
            if self.winner == "white":
                self.white_ai.learn_from_game("win")
                self.black_ai.learn_from_game("loss")
            elif self.winner == "black":
                self.white_ai.learn_from_game("loss")
                self.black_ai.learn_from_game("win")
            else:
                # Match nul
                self.white_ai.learn_from_game("draw")
                self.black_ai.learn_from_game("draw")
        elif self.white_ai:
            if self.winner == "white":
                self.white_ai.learn_from_game("win")
            elif self.winner == "black":
                self.white_ai.learn_from_game("loss")
            else:
                self.white_ai.learn_from_game("draw")
        elif self.black_ai:
            if self.winner == "black":
                self.black_ai.learn_from_game("win")
            elif self.winner == "white":
                self.black_ai.learn_from_game("loss")
            else:
                self.black_ai.learn_from_game("draw")
                
    def save_game_state(self):
        """Sauvegarde l'état actuel de la partie."""
        import os
        import json
        from datetime import datetime
        
        # Créer le dossier de sauvegarde s'il n'existe pas
        save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_games')
        os.makedirs(save_dir, exist_ok=True)
        
        # Créer un identifiant unique pour la partie
        game_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Préparer les données à sauvegarder
        game_data = {
            "board": self.board.to_dict(),
            "turn": self.turn,
            "opponent": self.opponent,
            "game_over": self.game_over,
            "winner": self.winner,
            "white_player_type": self.white_player_type,
            "black_player_type": self.black_player_type,
            "history": self.board.history.moves.to_dict(orient='records') if hasattr(self.board, 'history') and hasattr(self.board.history, 'moves') else [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Sauvegarder les données
        save_path = os.path.join(save_dir, f"game_{game_id}.json")
        try:
            with open(save_path, 'w') as f:
                json.dump(game_data, f, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la partie: {e}")
    
    def play_ai_turn(self):
        """Fait jouer l'IA pour le tour actuel."""
        try:
            print(f"Début du tour de l'IA ({self.turn})")
            
            if self.game_over:
                print("La partie est terminée, l'IA ne peut pas jouer")
                return False, "La partie est terminée"
            
            ai = self.white_ai if self.turn == "white" else self.black_ai
            if not ai:
                print(f"Pas d'IA configurée pour le joueur {self.turn}")
                return False, "Pas d'IA pour ce joueur"
            
            print(f"Recherche du meilleur coup pour l'IA {self.turn} (difficulté: {ai.difficulty})")
            # Obtenir le meilleur mouvement de l'IA
            best_move = ai.get_best_move(self.board)
            if not best_move:
                print("L'IA n'a pas trouvé de mouvement valide")
                return False, "L'IA ne trouve pas de mouvement valide"
            
            start_pos, end_pos = best_move
            print(f"Meilleur coup trouvé: {start_pos} → {end_pos}")
            
            # Convertir les positions en notation d'échecs
            start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
            end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
            print(f"Notation d'échecs: {start_notation} → {end_notation}")
            
            # Jouer le coup
            print(f"L'IA joue: {start_notation} → {end_notation}")
            success, message = self.play_turn(start_notation, end_notation)
            
            if success:
                print(f"Coup de l'IA réussi: {message}")
                return True, f"L'IA a joué {start_notation} vers {end_notation}. {message}"
            else:
                print(f"Échec du coup de l'IA: {message}")
                return False, f"Erreur lors du coup de l'IA: {message}"
                
        except Exception as e:
            import traceback
            print(f"Erreur lors du tour de l'IA: {str(e)}")
            print(traceback.format_exc())
            return False, f"Erreur interne de l'IA: {str(e)}"

    def get_game_state(self):
        """Retourne l'état actuel du jeu."""
        # Utiliser to_list au lieu de get_display_board().to_dict() pour obtenir un tableau 2D simple
        return {
            "board": self.board.to_list(),
            "turn": self.turn,
            "game_over": self.game_over,
            "winner": self.winner,
            "white_player_type": self.white_player_type,
            "black_player_type": self.black_player_type
        }
    
    def set_player_type(self, color, player_type, ai_difficulty="medium"):
        """Change le type de joueur (humain ou IA)."""
        if color == "white":
            self.white_player_type = player_type
            if player_type == "ai":
                self.white_ai = AI(color="white", difficulty=ai_difficulty)
            else:
                self.white_ai = None
        else:
            self.black_player_type = player_type
            if player_type == "ai":
                self.black_ai = AI(color="black", difficulty=ai_difficulty)
            else:
                self.black_ai = None
        
        # Si c'est le tour de l'IA après le changement, jouer automatiquement
        if not self.game_over:
            if (self.turn == "white" and self.white_player_type == "ai") or \
               (self.turn == "black" and self.black_player_type == "ai"):
                return self.play_ai_turn()
        
        return True, "Type de joueur modifié"