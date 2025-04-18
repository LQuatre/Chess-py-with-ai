import time
import json
import os
import random
import datetime
import numpy as np
from game.move import Move
import pickle

class AI:
    def __init__(self, color="black", difficulty="easy"):
        self.color = color
        self.difficulty = difficulty  # "easy", "medium", "hard"
        self.piece_values = {
            "Pawn": 100,
            "Knight": 320,
            "Bishop": 330,
            "Rook": 500,
            "Queen": 900,
            "King": 20000
        }
        
        # Tables de valeurs positionnelles pour chaque type de pièce
        self.position_tables = {
            "Pawn": [
                [0,  0,  0,  0,  0,  0,  0,  0],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [5,  5, 10, 25, 25, 10,  5,  5],
                [0,  0,  0, 20, 20,  0,  0,  0],
                [5, -5,-10,  0,  0,-10, -5,  5],
                [5, 10, 10,-20,-20, 10, 10,  5],
                [0,  0,  0,  0,  0,  0,  0,  0]
            ],
            "Knight": [
                [-50,-40,-30,-30,-30,-30,-40,-50],
                [-40,-20,  0,  0,  0,  0,-20,-40],
                [-30,  0, 10, 15, 15, 10,  0,-30],
                [-30,  5, 15, 20, 20, 15,  5,-30],
                [-30,  0, 15, 20, 20, 15,  0,-30],
                [-30,  5, 10, 15, 15, 10,  5,-30],
                [-40,-20,  0,  5,  5,  0,-20,-40],
                [-50,-40,-30,-30,-30,-30,-40,-50]
            ],
            "Bishop": [
                [-20,-10,-10,-10,-10,-10,-10,-20],
                [-10,  0,  0,  0,  0,  0,  0,-10],
                [-10,  0, 10, 10, 10, 10,  0,-10],
                [-10,  5,  5, 10, 10,  5,  5,-10],
                [-10,  0,  5, 10, 10,  5,  0,-10],
                [-10,  5,  5,  5,  5,  5,  5,-10],
                [-10,  0,  5,  0,  0,  5,  0,-10],
                [-20,-10,-10,-10,-10,-10,-10,-20]
            ],
            "Rook": [
                [0,  0,  0,  0,  0,  0,  0,  0],
                [5, 10, 10, 10, 10, 10, 10,  5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [0,  0,  0,  5,  5,  0,  0,  0]
            ],
            "Queen": [
                [-20,-10,-10, -5, -5,-10,-10,-20],
                [-10,  0,  0,  0,  0,  0,  0,-10],
                [-10,  0,  5,  5,  5,  5,  0,-10],
                [-5,  0,  5,  5,  5,  5,  0, -5],
                [0,  0,  5,  5,  5,  5,  0, -5],
                [-10,  5,  5,  5,  5,  5,  0,-10],
                [-10,  0,  5,  0,  0,  0,  0,-10],
                [-20,-10,-10, -5, -5,-10,-10,-20]
            ],
            "King": [
                [-30,-40,-40,-50,-50,-40,-40,-30],
                [-30,-40,-40,-50,-50,-40,-40,-30],
                [-30,-40,-40,-50,-50,-40,-40,-30],
                [-30,-40,-40,-50,-50,-40,-40,-30],
                [-20,-30,-30,-40,-40,-30,-30,-20],
                [-10,-20,-20,-20,-20,-20,-20,-10],
                [20, 20,  0,  0,  0,  0, 20, 20],
                [20, 30, 10,  0,  0, 10, 30, 20]
            ],
            "King_endgame": [
                [-50,-40,-30,-20,-20,-30,-40,-50],
                [-30,-20,-10,  0,  0,-10,-20,-30],
                [-30,-10, 20, 30, 30, 20,-10,-30],
                [-30,-10, 30, 40, 40, 30,-10,-30],
                [-30,-10, 30, 40, 40, 30,-10,-30],
                [-30,-10, 20, 30, 30, 20,-10,-30],
                [-30,-30,  0,  0,  0,  0,-30,-30],
                [-50,-30,-30,-30,-30,-30,-30,-50]
            ]
        }
        
        # Initialiser la table de transposition
        self.transposition_table = {}
        
        # Initialiser la base de données d'ouvertures
        self.opening_book = self.load_opening_book()
        
        # Initialiser la base de données d'apprentissage
        self.learning_data = self.load_learning_data()
        
        # Historique des parties pour l'apprentissage
        self.game_history = []
        
        # Nombre de nœuds évalués (pour les statistiques)
        self.nodes_evaluated = 0
        
        # Journal des chemins de pensée
        self.thought_log = []
        self.max_log_entries = 100  # Limiter le nombre d'entrées pour éviter une utilisation excessive de la mémoire
        
    def set_color(self, color):
        """Définit la couleur de l'IA."""
        self.color = color
        
    def set_difficulty(self, difficulty):
        """Définit la difficulté de l'IA."""
        self.difficulty = difficulty

    def get_best_move(self, board):
        """Sélectionne le meilleur mouvement en fonction de la difficulté."""
        # Réinitialiser les statistiques et le journal de pensées
        self.nodes_evaluated = 0
        self.thought_log = []
        
        # Ajouter une entrée au journal
        self.log_thought("Début de la recherche du meilleur coup pour les " + self.color)
        
        # Vérifier si nous sommes dans l'ouverture
        opening_move = self.get_opening_move(board)
        if opening_move:
            self.log_thought("Coup d'ouverture trouvé dans la base de données")
            start_pos, end_pos = opening_move
            start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
            end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
            self.log_thought(f"Joue le coup d'ouverture: {start_notation} → {end_notation}")
            return opening_move
            
        # Sinon, utiliser l'algorithme approprié selon la difficulté
        if self.difficulty == "easy":
            self.log_thought("Utilisation de l'algorithme de sélection semi-aléatoire (difficulté: facile)")
            move = self.get_smart_random_move(board)
        elif self.difficulty == "medium":
            self.log_thought("Utilisation de l'algorithme minimax avec profondeur 3 (difficulté: moyenne)")
            move = self.get_minimax_move(board, depth=3)
        else:  # hard
            self.log_thought("Utilisation de l'algorithme minimax avec profondeur 6 (difficulté: difficile)")
            move = self.get_minimax_move(board, depth=6)
            
        if move:
            start_pos, end_pos = move
            start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
            end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
            self.log_thought(f"Meilleur coup trouvé: {start_notation} → {end_notation}")
            self.log_thought(f"Nombre de nœuds évalués: {self.nodes_evaluated}")
        else:
            self.log_thought("Aucun coup valide trouvé!")
            
        return move
    
    def get_smart_random_move(self, board):
        """Sélectionne un mouvement semi-aléatoire avec une préférence pour les bons coups."""
        all_moves = self.get_all_valid_moves(board, self.color)
        if not all_moves:
            return None
            
        # Évaluer chaque mouvement
        move_scores = []
        for start_pos, end_pos in all_moves:
            # Simuler le mouvement
            temp_board = board.copy()
            start_row, start_col = start_pos
            end_row, end_col = end_pos
            
            # Exécuter le mouvement sur le plateau temporaire
            piece = temp_board.get_piece(start_row, start_col)
            temp_board.set_piece(end_row, end_col, piece)
            temp_board.set_piece(start_row, start_col, "")
            
            # Évaluer la position résultante
            score = self.evaluate_board(temp_board)
            move_scores.append((score, (start_pos, end_pos)))
        
        # Trier les mouvements par score
        move_scores.sort(reverse=True)
        
        # Sélectionner un mouvement parmi les 40% meilleurs
        top_moves = move_scores[:max(1, len(move_scores) // 3)]
        return random.choice([move for _, move in top_moves])
    
    def get_opening_move(self, board):
        """Cherche un mouvement dans la base de données d'ouvertures."""
        if not self.opening_book:
            return None
            
        # Convertir le plateau en une représentation FEN simplifiée
        board_state = self.get_board_state(board)
        
        # Chercher dans la base de données d'ouvertures
        if board_state in self.opening_book:
            moves = self.opening_book[board_state]
            # Choisir le meilleur mouvement ou un mouvement aléatoire parmi les meilleurs
            if moves:
                if random.random() < 0.8:  # 80% de chance de choisir le meilleur mouvement
                    best_move = max(moves.items(), key=lambda x: x[1])[0]
                    start_pos, end_pos = self.parse_move_notation(best_move)
                    return (start_pos, end_pos)
                else:
                    # Choisir un mouvement aléatoire parmi les mouvements connus
                    move = random.choice(list(moves.keys()))
                    start_pos, end_pos = self.parse_move_notation(move)
                    return (start_pos, end_pos)
        
        return None
    
    def parse_move_notation(self, move_notation):
        """Convertit une notation de mouvement (ex: 'e2e4') en positions de départ et d'arrivée."""
        start_col = ord(move_notation[0]) - ord('a')
        start_row = 8 - int(move_notation[1])
        end_col = ord(move_notation[2]) - ord('a')
        end_row = 8 - int(move_notation[3])
        
        return ((start_row, start_col), (end_row, end_col))
    
    def get_board_state(self, board):
        """Convertit le plateau en une représentation FEN simplifiée."""
        fen = ""
        for row in range(8):
            empty = 0
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece == "":
                    empty += 1
                else:
                    if empty > 0:
                        fen += str(empty)
                        empty = 0
                    piece_type = piece.__class__.__name__[0]
                    if piece.color == "white":
                        fen += piece_type.upper()
                    else:
                        fen += piece_type.lower()
            if empty > 0:
                fen += str(empty)
            if row < 7:
                fen += "/"
        
        # Ajouter le tour actuel
        fen += " " + board.turn[0]
        
        return fen
    
    def get_minimax_move(self, board, depth=5):
        """Utilise l'algorithme minimax avec élagage alpha-beta et table de transposition pour trouver le meilleur mouvement."""
        # Réinitialiser la table de transposition pour cette recherche
        self.transposition_table = {}
        
        all_moves = self.get_all_valid_moves(board, self.color)
        if not all_moves:
            return None
            
        best_score = -float('inf')
        best_move = None
        alpha = -float('inf')
        beta = float('inf')
        
        # Trier les mouvements pour améliorer l'élagage alpha-beta
        sorted_moves = self.order_moves(board, all_moves)
        
        # Liste pour stocker les mouvements sûrs (qui ne donnent pas de pièces)
        safe_moves = []
        
        for start_pos, end_pos in sorted_moves:
            # Simuler le mouvement
            temp_board = board.copy()
            start_row, start_col = start_pos
            end_row, end_col = end_pos
            
            # Exécuter le mouvement sur le plateau temporaire
            piece = temp_board.get_piece(start_row, start_col)
            temp_board.set_piece(end_row, end_col, piece)
            temp_board.set_piece(start_row, start_col, "")
            
            # Vérifier si ce coup met une pièce en danger sans compensation
            is_safe = self.is_move_safe(board, temp_board, start_pos, end_pos, piece)
            
            # Évaluer le score avec minimax
            score = -self.minimax(temp_board, depth-1, -beta, -alpha, False)
            
            # Si le coup est sûr, l'ajouter à la liste des coups sûrs
            if is_safe:
                safe_moves.append((score, (start_pos, end_pos)))
            
            if score > best_score:
                best_score = score
                best_move = (start_pos, end_pos)
            
            alpha = max(alpha, best_score)
        
        # Si nous avons des coups sûrs, choisir le meilleur parmi eux
        if safe_moves and len(safe_moves) > 0:
            safe_moves.sort(reverse=True)  # Trier par score décroissant
            best_safe_score, best_safe_move = safe_moves[0]
            
            # Si le meilleur coup sûr n'est pas trop inférieur au meilleur coup global, le préférer
            if best_safe_score > best_score - 200:  # Tolérance de 200 points
                self.log_thought(f"Choix d'un coup plus sûr: {best_safe_score:.1f} vs {best_score:.1f}")
                best_move = best_safe_move
        
        # Enregistrer le mouvement dans l'historique pour l'apprentissage
        if best_move:
            self.record_move(board, best_move, best_score)
            
        return best_move if best_move else (sorted_moves[0] if sorted_moves else None)
        
    def is_move_safe(self, original_board, new_board, start_pos, end_pos, moved_piece):
        """Vérifie si un coup est sûr (ne donne pas de pièces gratuitement)."""
        # Obtenir la valeur de la pièce déplacée
        piece_type = moved_piece.__class__.__name__
        piece_value = self.piece_values.get(piece_type, 0)
        
        # Obtenir les pièces attaquées après le coup
        attacked_pieces = self.get_attacked_pieces(new_board)
        
        # Vérifier si la pièce déplacée est attaquée et non défendue
        end_row, end_col = end_pos
        if (end_row, end_col) in attacked_pieces:
            # Vérifier si la pièce est défendue
            defended_pieces = self.get_defended_pieces(new_board)
            is_defended = (end_row, end_col) in defended_pieces
            
            if not is_defended:
                # La pièce est attaquée et non défendue
                self.log_thought(f"Coup dangereux: {piece_type} en {chr(end_col + ord('a'))}{8-end_row} serait attaqué et non défendu")
                return False
            
            # Même si elle est défendue, vérifier si l'échange est favorable
            attackers = attacked_pieces[(end_row, end_col)]
            lowest_attacker_value = float('inf')
            
            for attacker_row, attacker_col in attackers:
                attacker = new_board.get_piece(attacker_row, attacker_col)
                if attacker and hasattr(attacker, '__class__'):
                    attacker_type = attacker.__class__.__name__
                    attacker_value = self.piece_values.get(attacker_type, 0)
                    lowest_attacker_value = min(lowest_attacker_value, attacker_value)
            
            # Si l'attaquant le moins cher vaut moins que notre pièce, l'échange est défavorable
            if lowest_attacker_value < piece_value:
                self.log_thought(f"Échange défavorable: {piece_type} ({piece_value}) contre {lowest_attacker_value}")
                return False
        
        return True
    
    def order_moves(self, board, moves):
        """Trie les mouvements pour améliorer l'élagage alpha-beta."""
        move_scores = []
        
        # Calculer les pièces attaquées et défendues
        attacked_pieces = self.get_attacked_pieces(board)
        
        for start_pos, end_pos in moves:
            score = 0
            start_row, start_col = start_pos
            end_row, end_col = end_pos
            
            # Priorité aux captures
            target_piece = board.get_piece(end_row, end_col)
            if target_piece and hasattr(target_piece, 'color') and target_piece.color != self.color:
                piece_type = target_piece.__class__.__name__
                target_value = self.piece_values.get(piece_type, 0)
                
                # Évaluer l'échange
                piece = board.get_piece(start_row, start_col)
                if piece and hasattr(piece, '__class__'):
                    piece_type = piece.__class__.__name__
                    piece_value = self.piece_values.get(piece_type, 0)
                    
                    # Vérifier si la pièce qui capture sera elle-même capturée
                    temp_board = board.copy()
                    temp_board.set_piece(end_row, end_col, piece)
                    temp_board.set_piece(start_row, start_col, "")
                    
                    # Vérifier si la case d'arrivée est attaquée
                    future_attacked = self.get_attacked_pieces(temp_board)
                    if (end_row, end_col) in future_attacked:
                        # Échange défavorable
                        if piece_value > target_value:
                            score += target_value - piece_value  # Pénalité pour l'échange défavorable
                        else:
                            score += 10 * target_value  # Bonus pour l'échange favorable
                    else:
                        # Capture sans risque
                        score += 10 * target_value
                else:
                    score += 10 * target_value
            
            # Priorité aux promotions de pions
            piece = board.get_piece(start_row, start_col)
            if piece and hasattr(piece, '__class__') and piece.__class__.__name__ == 'Pawn':
                if (piece.color == 'white' and end_row == 0) or (piece.color == 'black' and end_row == 7):
                    score += 900  # Valeur d'une dame
            
            # Éviter de déplacer des pièces déjà attaquées vers des cases non défendues
            if (start_row, start_col) in attacked_pieces:
                # Simuler le mouvement
                temp_board = board.copy()
                temp_board.set_piece(end_row, end_col, piece)
                temp_board.set_piece(start_row, start_col, "")
                
                # Vérifier si la case d'arrivée est attaquée
                future_attacked = self.get_attacked_pieces(temp_board)
                future_defended = self.get_defended_pieces(temp_board)
                
                if (end_row, end_col) in future_attacked and (end_row, end_col) not in future_defended:
                    # La pièce serait en danger
                    score -= 500
            
            # Priorité aux mouvements vers le centre
            center_distance = abs(3.5 - end_row) + abs(3.5 - end_col)
            score -= center_distance
            
            # Utiliser les données d'apprentissage si disponibles
            move_key = f"{start_row}{start_col}{end_row}{end_col}"
            if move_key in self.learning_data:
                score += self.learning_data[move_key] * 5
            
            move_scores.append((score, (start_pos, end_pos)))
        
        # Trier les mouvements par score décroissant
        move_scores.sort(reverse=True)
        return [move for _, move in move_scores]
    
    def log_thought(self, thought):
        """Ajoute une entrée au journal des chemins de pensée."""
        # Ajouter un horodatage
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Ajouter l'entrée au journal
        self.thought_log.append(f"[{timestamp}] {thought}")
        
        # Limiter la taille du journal
        if len(self.thought_log) > self.max_log_entries:
            self.thought_log.pop(0)
    
    def minimax(self, board, depth, alpha, beta, is_maximizing):
        """Implémentation de l'algorithme minimax avec élagage alpha-beta et table de transposition."""
        # Incrémenter le compteur de nœuds
        self.nodes_evaluated += 1
        
        # Enregistrer la pensée seulement pour les niveaux supérieurs (pour éviter trop de logs)
        if depth >= 3:
            player = self.color if is_maximizing else ("white" if self.color == "black" else "black")
            self.log_thought(f"Analyse à la profondeur {depth} pour {player}, α={alpha:.1f}, β={beta:.1f}")
        
        # Vérifier la table de transposition
        board_hash = self.hash_board(board)
        if board_hash in self.transposition_table:
            stored_depth, stored_score, stored_flag = self.transposition_table[board_hash]
            if stored_depth >= depth:
                if stored_flag == 'exact':
                    if depth >= 3:
                        self.log_thought(f"Position trouvée dans la table de transposition avec score exact: {stored_score:.1f}")
                    return stored_score
                elif stored_flag == 'lowerbound' and stored_score > alpha:
                    alpha = stored_score
                    if depth >= 3:
                        self.log_thought(f"Borne inférieure trouvée dans la table: {alpha:.1f}")
                elif stored_flag == 'upperbound' and stored_score < beta:
                    beta = stored_score
                    if depth >= 3:
                        self.log_thought(f"Borne supérieure trouvée dans la table: {beta:.1f}")
                
                if alpha >= beta:
                    if depth >= 3:
                        self.log_thought(f"Coupure alpha-beta avec score: {stored_score:.1f}")
                    return stored_score
        
        # Vérifier les conditions de terminaison
        if depth == 0:
            score = self.quiescence_search(board, alpha, beta, is_maximizing, 3)
            if depth >= 3:
                self.log_thought(f"Recherche de quiescence terminée avec score: {score:.1f}")
            return score
        
        # Vérifier si le jeu est terminé
        game_status = board.check_game_status()
        if game_status != "In Progress":
            if game_status == "Checkmate":
                score = -20000 if is_maximizing else 20000
                if depth >= 3:
                    self.log_thought(f"Position d'échec et mat détectée, score: {score}")
                return score
            else:  # Stalemate
                if depth >= 3:
                    self.log_thought("Position de pat détectée, score: 0")
                return 0
        
        # Récupérer les mouvements valides
        color = self.color if is_maximizing else ("white" if self.color == "black" else "black")
        all_moves = self.get_all_valid_moves(board, color)
        
        # Trier les mouvements pour améliorer l'élagage
        sorted_moves = self.order_moves(board, all_moves)
        
        if depth >= 3:
            self.log_thought(f"Analyse de {len(sorted_moves)} coups possibles")
        
        if is_maximizing:
            max_score = -float('inf')
            best_move = None
            
            for start_pos, end_pos in sorted_moves:
                # Convertir en notation d'échecs pour le log
                if depth >= 3:
                    start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
                    end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
                    self.log_thought(f"Évaluation du coup {start_notation} → {end_notation}")
                
                # Simuler le mouvement
                temp_board = board.copy()
                start_row, start_col = start_pos
                end_row, end_col = end_pos
                
                # Exécuter le mouvement sur le plateau temporaire
                piece = temp_board.get_piece(start_row, start_col)
                temp_board.set_piece(end_row, end_col, piece)
                temp_board.set_piece(start_row, start_col, "")
                
                score = self.minimax(temp_board, depth-1, alpha, beta, False)
                
                if score > max_score:
                    max_score = score
                    best_move = (start_pos, end_pos)
                    if depth >= 3:
                        start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
                        end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
                        self.log_thought(f"Nouveau meilleur coup: {start_notation} → {end_notation} avec score {score:.1f}")
                
                alpha = max(alpha, max_score)
                
                if beta <= alpha:
                    if depth >= 3:
                        self.log_thought(f"Coupure alpha-beta (α={alpha:.1f}, β={beta:.1f})")
                    break
                    
            # Stocker le résultat dans la table de transposition
            if max_score <= alpha:
                flag = 'upperbound'
            elif max_score >= beta:
                flag = 'lowerbound'
            else:
                flag = 'exact'
            self.transposition_table[board_hash] = (depth, max_score, flag)
            
            if depth >= 3 and best_move:
                start_pos, end_pos = best_move
                start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
                end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
                self.log_thought(f"Meilleur coup à la profondeur {depth}: {start_notation} → {end_notation} (score: {max_score:.1f})")
            
            return max_score
        else:
            min_score = float('inf')
            best_move = None
            
            for start_pos, end_pos in sorted_moves:
                # Convertir en notation d'échecs pour le log
                if depth >= 3:
                    start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
                    end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
                    self.log_thought(f"Évaluation du coup {start_notation} → {end_notation}")
                
                # Simuler le mouvement
                temp_board = board.copy()
                start_row, start_col = start_pos
                end_row, end_col = end_pos
                
                # Exécuter le mouvement sur le plateau temporaire
                piece = temp_board.get_piece(start_row, start_col)
                temp_board.set_piece(end_row, end_col, piece)
                temp_board.set_piece(start_row, start_col, "")
                
                score = self.minimax(temp_board, depth-1, alpha, beta, True)
                
                if score < min_score:
                    min_score = score
                    best_move = (start_pos, end_pos)
                    if depth >= 3:
                        start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
                        end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
                        self.log_thought(f"Nouveau meilleur coup: {start_notation} → {end_notation} avec score {score:.1f}")
                
                beta = min(beta, min_score)
                
                if beta <= alpha:
                    if depth >= 3:
                        self.log_thought(f"Coupure alpha-beta (α={alpha:.1f}, β={beta:.1f})")
                    break
            
            # Stocker le résultat dans la table de transposition
            if min_score <= alpha:
                flag = 'upperbound'
            elif min_score >= beta:
                flag = 'lowerbound'
            else:
                flag = 'exact'
            self.transposition_table[board_hash] = (depth, min_score, flag)
            
            if depth >= 3 and best_move:
                start_pos, end_pos = best_move
                start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
                end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
                self.log_thought(f"Meilleur coup à la profondeur {depth}: {start_notation} → {end_notation} (score: {min_score:.1f})")
            
            return min_score
    
    def quiescence_search(self, board, alpha, beta, is_maximizing, depth=3):
        """Recherche de quiescence pour éviter l'effet d'horizon."""
        # Évaluation de base
        stand_pat = self.evaluate_board(board)
        
        # Vérifier les conditions de terminaison
        if depth == 0:
            return stand_pat
            
        if is_maximizing:
            if stand_pat >= beta:
                return beta
            if alpha < stand_pat:
                alpha = stand_pat
                
            # Récupérer uniquement les captures
            captures = self.get_capture_moves(board, self.color)
            
            for start_pos, end_pos in captures:
                # Simuler le mouvement
                temp_board = board.copy()
                start_row, start_col = start_pos
                end_row, end_col = end_pos
                
                # Exécuter le mouvement sur le plateau temporaire
                piece = temp_board.get_piece(start_row, start_col)
                temp_board.set_piece(end_row, end_col, piece)
                temp_board.set_piece(start_row, start_col, "")
                
                score = self.quiescence_search(temp_board, alpha, beta, False, depth-1)
                
                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
            
            return alpha
        else:
            if stand_pat <= alpha:
                return alpha
            if beta > stand_pat:
                beta = stand_pat
                
            # Récupérer uniquement les captures
            opponent_color = "white" if self.color == "black" else "black"
            captures = self.get_capture_moves(board, opponent_color)
            
            for start_pos, end_pos in captures:
                # Simuler le mouvement
                temp_board = board.copy()
                start_row, start_col = start_pos
                end_row, end_col = end_pos
                
                # Exécuter le mouvement sur le plateau temporaire
                piece = temp_board.get_piece(start_row, start_col)
                temp_board.set_piece(end_row, end_col, piece)
                temp_board.set_piece(start_row, start_col, "")
                
                score = self.quiescence_search(temp_board, alpha, beta, True, depth-1)
                
                if score <= alpha:
                    return alpha
                if score < beta:
                    beta = score
            
            return beta
    
    def get_capture_moves(self, board, color):
        """Récupère tous les mouvements de capture pour une couleur donnée."""
        captures = []
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, 'color') and piece.color == color:
                    valid_moves = board.get_valid_moves(row, col)
                    for end_row, end_col in valid_moves:
                        target = board.get_piece(end_row, end_col)
                        if target and hasattr(target, 'color') and target.color != color:
                            captures.append(((row, col), (end_row, end_col)))
        
        return captures
        
    def get_attacked_pieces(self, board):
        """Identifie les pièces attaquées par l'adversaire."""
        attacked = {}
        opponent_color = "white" if self.color == "black" else "black"
        
        # Trouver toutes les cases attaquées par l'adversaire
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, 'color') and piece.color == opponent_color:
                    valid_moves = board.get_valid_moves(row, col)
                    for end_row, end_col in valid_moves:
                        target = board.get_piece(end_row, end_col)
                        if target and hasattr(target, 'color') and target.color == self.color:
                            # Ajouter à la liste des pièces attaquées
                            key = (end_row, end_col)
                            if key not in attacked:
                                attacked[key] = []
                            attacked[key].append((row, col))
        
        return attacked
        
    def get_defended_pieces(self, board):
        """Identifie les pièces défendues par des pièces alliées."""
        defended = {}
        
        # Trouver toutes les cases défendues par des pièces alliées
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, 'color') and piece.color == self.color:
                    valid_moves = board.get_valid_moves(row, col)
                    for end_row, end_col in valid_moves:
                        target = board.get_piece(end_row, end_col)
                        if target and hasattr(target, 'color') and target.color == self.color:
                            # Ajouter à la liste des pièces défendues
                            key = (end_row, end_col)
                            if key not in defended:
                                defended[key] = []
                            defended[key].append((row, col))
        
        return defended
    
    def hash_board(self, board):
        """Crée un hash du plateau pour la table de transposition."""
        board_str = ""
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece == "":
                    board_str += "."
                else:
                    piece_type = piece.__class__.__name__[0]
                    if piece.color == "white":
                        board_str += piece_type.upper()
                    else:
                        board_str += piece_type.lower()
        
        board_str += board.turn[0]  # Ajouter le tour actuel
        return hash(board_str)
    
    def evaluate_board(self, board):
        """Évalue la position actuelle du plateau avec une fonction d'évaluation avancée."""
        if board.check_game_status() == "Checkmate":
            # Si c'est échec et mat, retourner une valeur extrême
            if board.turn == self.color:
                return -20000  # Nous avons perdu
            else:
                return 20000   # Nous avons gagné
        
        if board.check_game_status() == "Stalemate":
            return 0  # Match nul
        
        score = 0
        piece_count = {"white": 0, "black": 0}
        
        # Calculer les pièces attaquées et défendues
        attacked_pieces = self.get_attacked_pieces(board)
        defended_pieces = self.get_defended_pieces(board)
        
        # Évaluer la valeur matérielle et positionnelle
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, 'color'):
                    piece_type = piece.__class__.__name__
                    piece_count[piece.color] += 1
                    
                    # Valeur de base de la pièce
                    piece_value = self.piece_values.get(piece_type, 0)
                    
                    # Ajuster le score en fonction de la couleur
                    if piece.color == self.color:
                        score += piece_value
                        
                        # Valeur positionnelle
                        position_table = self.position_tables.get(piece_type, [[0]*8 for _ in range(8)])
                        
                        # Pour les pions noirs, inverser la table
                        if piece.color == "black" and piece_type == "Pawn":
                            position_value = position_table[7-row][col]
                        # Pour les pions blancs, utiliser la table telle quelle
                        elif piece.color == "white" and piece_type == "Pawn":
                            position_value = position_table[row][col]
                        # Pour les autres pièces, utiliser la table appropriée
                        else:
                            position_value = position_table[row][col]
                        
                        score += position_value * 0.1
                    else:
                        score -= piece_value
                        
                        # Valeur positionnelle pour l'adversaire
                        position_table = self.position_tables.get(piece_type, [[0]*8 for _ in range(8)])
                        
                        # Pour les pions noirs, inverser la table
                        if piece.color == "black" and piece_type == "Pawn":
                            position_value = position_table[7-row][col]
                        # Pour les pions blancs, utiliser la table telle quelle
                        elif piece.color == "white" and piece_type == "Pawn":
                            position_value = position_table[row][col]
                        # Pour les autres pièces, utiliser la table appropriée
                        else:
                            position_value = position_table[row][col]
                        
                        score -= position_value * 0.1
        
        # Déterminer si nous sommes en fin de partie
        is_endgame = (piece_count["white"] + piece_count["black"] <= 10)
        
        # Bonus pour la mobilité (nombre de mouvements possibles)
        my_moves = len(self.get_all_valid_moves(board, self.color))
        opponent_color = "white" if self.color == "black" else "black"
        opponent_moves = len(self.get_all_valid_moves(board, opponent_color))
        score += 0.1 * (my_moves - opponent_moves)
        
        # Bonus pour le contrôle du centre
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        for row, col in center_squares:
            piece = board.get_piece(row, col)
            if piece and hasattr(piece, 'color'):
                if piece.color == self.color:
                    score += 10
                else:
                    score -= 10
        
        # Pénalité pour les pions doublés
        for col in range(8):
            white_pawns = 0
            black_pawns = 0
            for row in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, '__class__') and piece.__class__.__name__ == 'Pawn':
                    if piece.color == "white":
                        white_pawns += 1
                    else:
                        black_pawns += 1
            
            # Pénaliser les pions doublés
            if white_pawns > 1:
                if self.color == "white":
                    score -= (white_pawns - 1) * 20
                else:
                    score += (white_pawns - 1) * 20
            
            if black_pawns > 1:
                if self.color == "black":
                    score -= (black_pawns - 1) * 20
                else:
                    score += (black_pawns - 1) * 20
        
        # Bonus pour les pions passés
        for col in range(8):
            for row in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, '__class__') and piece.__class__.__name__ == 'Pawn':
                    is_passed = True
                    
                    # Vérifier s'il y a des pions adverses qui peuvent bloquer
                    if piece.color == "white":
                        for r in range(row-1, -1, -1):  # Vérifier devant le pion blanc
                            for c in range(max(0, col-1), min(8, col+2)):
                                p = board.get_piece(r, c)
                                if p and hasattr(p, '__class__') and p.__class__.__name__ == 'Pawn' and p.color == "black":
                                    is_passed = False
                                    break
                    else:  # piece.color == "black"
                        for r in range(row+1, 8):  # Vérifier devant le pion noir
                            for c in range(max(0, col-1), min(8, col+2)):
                                p = board.get_piece(r, c)
                                if p and hasattr(p, '__class__') and p.__class__.__name__ == 'Pawn' and p.color == "white":
                                    is_passed = False
                                    break
                    
                    if is_passed:
                        # Bonus pour les pions passés, plus important en fin de partie
                        if piece.color == self.color:
                            # Plus le pion est avancé, plus le bonus est important
                            rank_bonus = 7 - row if piece.color == "white" else row
                            score += (20 + rank_bonus * 10) * (2 if is_endgame else 1)
                        else:
                            rank_bonus = 7 - row if piece.color == "white" else row
                            score -= (20 + rank_bonus * 10) * (2 if is_endgame else 1)
        
        # Bonus pour la sécurité du roi
        for color in ["white", "black"]:
            king_pos = board.find_king(color)
            if king_pos:
                king_row, king_col = king_pos
                
                # Pénalité pour le roi exposé
                if is_endgame:
                    # En fin de partie, le roi doit être actif
                    if color == self.color:
                        # Distance au centre
                        center_distance = abs(3.5 - king_row) + abs(3.5 - king_col)
                        score -= center_distance * 10
                    else:
                        center_distance = abs(3.5 - king_row) + abs(3.5 - king_col)
                        score += center_distance * 10
                else:
                    # En milieu de partie, le roi doit être protégé
                    if color == self.color:
                        # Vérifier les cases autour du roi
                        king_safety = 0
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                if dr == 0 and dc == 0:
                                    continue
                                r, c = king_row + dr, king_col + dc
                                if 0 <= r < 8 and 0 <= c < 8:
                                    piece = board.get_piece(r, c)
                                    if piece and hasattr(piece, 'color') and piece.color == color:
                                        king_safety += 1
                        
                        score += king_safety * 10
                    else:
                        # Vérifier les cases autour du roi adverse
                        king_safety = 0
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                if dr == 0 and dc == 0:
                                    continue
                                r, c = king_row + dr, king_col + dc
                                if 0 <= r < 8 and 0 <= c < 8:
                                    piece = board.get_piece(r, c)
                                    if piece and hasattr(piece, 'color') and piece.color == color:
                                        king_safety += 1
                        
                        score -= king_safety * 10
        
        # Vérifier si le roi est en échec
        if board.is_king_in_check(self.color):
            score -= 50  # Pénalité pour être en échec
        
        if board.is_king_in_check(opponent_color):
            score += 50  # Bonus pour mettre l'adversaire en échec
            
        # Pénaliser les pièces attaquées et non défendues
        for (row, col), attackers in attacked_pieces.items():
            piece = board.get_piece(row, col)
            if piece and hasattr(piece, '__class__'):
                piece_type = piece.__class__.__name__
                piece_value = self.piece_values.get(piece_type, 0)
                
                # Vérifier si la pièce est défendue
                is_defended = (row, col) in defended_pieces
                
                # Pénalité plus forte pour les pièces non défendues
                if not is_defended:
                    score -= piece_value * 0.3  # Pénalité sévère pour les pièces en danger
                    self.log_thought(f"Pièce en danger non défendue: {piece_type} en {chr(col + ord('a'))}{8-row}")
                else:
                    # Évaluer l'échange
                    lowest_attacker_value = float('inf')
                    for attacker_row, attacker_col in attackers:
                        attacker = board.get_piece(attacker_row, attacker_col)
                        if attacker and hasattr(attacker, '__class__'):
                            attacker_type = attacker.__class__.__name__
                            attacker_value = self.piece_values.get(attacker_type, 0)
                            lowest_attacker_value = min(lowest_attacker_value, attacker_value)
                    
                    # Si l'échange est défavorable
                    if lowest_attacker_value < piece_value:
                        score -= (piece_value - lowest_attacker_value) * 0.2
                        self.log_thought(f"Échange défavorable possible: {piece_type} contre {lowest_attacker_value}")
        
        return score
    
    def get_all_valid_moves(self, board, color):
        """Récupère tous les mouvements valides pour une couleur donnée."""
        all_moves = []
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, 'color') and piece.color == color:
                    valid_moves = board.get_valid_moves(row, col)
                    for end_row, end_col in valid_moves:
                        all_moves.append(((row, col), (end_row, end_col)))
        
        return all_moves
    
    def record_move(self, board, move, score):
        """Enregistre un mouvement dans l'historique pour l'apprentissage."""
        board_state = self.get_board_state(board)
        start_pos, end_pos = move
        move_notation = f"{chr(start_pos[1] + ord('a'))}{8 - start_pos[0]}{chr(end_pos[1] + ord('a'))}{8 - end_pos[0]}"
        
        # Ajouter à l'historique de la partie
        self.game_history.append((board_state, move_notation, score))
        
        # Si nous avons une base de données d'ouvertures, mettre à jour
        if self.opening_book and len(self.game_history) <= 20:  # Limiter aux 20 premiers coups
            if board_state not in self.opening_book:
                self.opening_book[board_state] = {}
            
            if move_notation not in self.opening_book[board_state]:
                self.opening_book[board_state][move_notation] = 0
            
            # Mettre à jour le score du mouvement
            self.opening_book[board_state][move_notation] += 1
    
    def learn_from_game(self, result):
        """Apprend de la partie terminée."""
        if not self.game_history:
            return
            
        # Facteur d'apprentissage
        learning_rate = 0.1
        
        # Récompense en fonction du résultat
        if result == "win":
            reward = 1.0
        elif result == "draw":
            reward = 0.5
        else:  # loss
            reward = 0.0
        
        # Mettre à jour les données d'apprentissage
        for board_state, move_notation, _ in self.game_history:
            move_key = move_notation.replace(move_notation[0], str(ord(move_notation[0]) - ord('a'))).replace(move_notation[2], str(ord(move_notation[2]) - ord('a')))
            move_key = move_key.replace(move_notation[1], str(8 - int(move_notation[1]))).replace(move_notation[3], str(8 - int(move_notation[3])))
            
            if move_key not in self.learning_data:
                self.learning_data[move_key] = 0.5  # Valeur initiale neutre
            
            # Mettre à jour la valeur du mouvement
            self.learning_data[move_key] += learning_rate * (reward - self.learning_data[move_key])
        
        # Sauvegarder les données d'apprentissage
        self.save_learning_data()
        
        # Sauvegarder la base de données d'ouvertures
        self.save_opening_book()
        
        # Réinitialiser l'historique de la partie
        self.game_history = []
    
    def load_opening_book(self):
        """Charge la base de données d'ouvertures."""
        try:
            opening_book_path = os.path.join(os.path.dirname(__file__), 'opening_book.json')
            if os.path.exists(opening_book_path):
                with open(opening_book_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Erreur lors du chargement de la base de données d'ouvertures: {e}")
            return {}
    
    def save_opening_book(self):
        """Sauvegarde la base de données d'ouvertures."""
        try:
            opening_book_path = os.path.join(os.path.dirname(__file__), 'opening_book.json')
            with open(opening_book_path, 'w') as f:
                json.dump(self.opening_book, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la base de données d'ouvertures: {e}")
    
    def load_learning_data(self):
        """Charge les données d'apprentissage."""
        try:
            learning_data_path = os.path.join(os.path.dirname(__file__), 'learning_data.pkl')
            if os.path.exists(learning_data_path):
                with open(learning_data_path, 'rb') as f:
                    return pickle.load(f)
            return {}
        except Exception as e:
            print(f"Erreur lors du chargement des données d'apprentissage: {e}")
            return {}
    
    def save_learning_data(self):
        """Sauvegarde les données d'apprentissage."""
        try:
            learning_data_path = os.path.join(os.path.dirname(__file__), 'learning_data.pkl')
            with open(learning_data_path, 'wb') as f:
                pickle.dump(self.learning_data, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données d'apprentissage: {e}")
            
    def get_thought_log(self):
        """Retourne le journal des chemins de pensée."""
        return self.thought_log

# Test rapide
if __name__ == "__main__":
    from game.board import Board
    
    board = Board()
    ai = AI(color="black", difficulty="hard")
    best_move = ai.get_best_move(board)
    print(f"Meilleur mouvement: {best_move}")
    print(f"Nœuds évalués: {ai.nodes_evaluated}")
