import time
import json
import os
import random
import datetime
import numpy as np
import pandas as pd
import threading
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend which doesn't require a GUI
# Vérifier si nous sommes dans le thread principal
is_main_thread = threading.current_thread() is threading.main_thread()
import matplotlib.pyplot as plt
from game.move import Move
import pickle
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

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
        
        # Tables de valeurs positionnelles pour chaque type de pièce (converties en numpy arrays)
        self.position_tables = {
            "Pawn": np.array([
                [0,  0,  0,  0,  0,  0,  0,  0],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [5,  5, 10, 40, 40, 10,  5,  5],
                [0,  0,  5, 35, 35,  5,  0,  0],
                [5, -5,  0, 20, 20,  0, -5,  5],
                [5, 10, 10,-10,-10, 10, 10,  5],
                [0,  0,  0,  0,  0,  0,  0,  0]
            ]),
            "Knight": np.array([
                [-50,-40,-30,-30,-30,-30,-40,-50],
                [-40,-20,  0,  5,  5,  0,-20,-40],
                [-30,  0, 15, 20, 20, 15,  0,-30],
                [-30,  5, 20, 30, 30, 20,  5,-30],
                [-30,  0, 20, 30, 30, 20,  0,-30],
                [-30,  5, 15, 20, 20, 15,  5,-30],
                [-40,-20,  0,  5,  5,  0,-20,-40],
                [-50,-40,-30,-30,-30,-30,-40,-50]
            ]),
            "Bishop": np.array([
                [-20,-10,-10,-10,-10,-10,-10,-20],
                [-10,  0,  0,  0,  0,  0,  0,-10],
                [-10,  0, 15, 15, 15, 15,  0,-10],
                [-10,  5, 15, 20, 20, 15,  5,-10],
                [-10,  0, 15, 20, 20, 15,  0,-10],
                [-10,  5, 10, 10, 10, 10,  5,-10],
                [-10,  0,  5,  0,  0,  5,  0,-10],
                [-20,-10,-10,-10,-10,-10,-10,-20]
            ]),
            "Rook": np.array([
                [0,  0,  0,  0,  0,  0,  0,  0],
                [5, 10, 10, 10, 10, 10, 10,  5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [-5,  0,  0,  0,  0,  0,  0, -5],
                [0,  0,  0,  5,  5,  0,  0,  0]
            ]),
            "Queen": np.array([
                [-20,-10,-10, -5, -5,-10,-10,-20],
                [-10,  0,  0,  0,  0,  0,  0,-10],
                [-10,  0,  5,  5,  5,  5,  0,-10],
                [-5,  0,  5,  5,  5,  5,  0, -5],
                [0,  0,  5,  5,  5,  5,  0, -5],
                [-10,  5,  5,  5,  5,  5,  0,-10],
                [-10,  0,  5,  0,  0,  0,  0,-10],
                [-20,-10,-10, -5, -5,-10,-10,-20]
            ]),
            "King": np.array([
                [-30,-40,-40,-50,-50,-40,-40,-30],
                [-30,-40,-40,-50,-50,-40,-40,-30],
                [-30,-40,-40,-50,-50,-40,-40,-30],
                [-30,-40,-40,-50,-50,-40,-40,-30],
                [-20,-30,-30,-40,-40,-30,-30,-20],
                [-10,-20,-20,-20,-20,-20,-20,-10],
                [20, 20,  0,  0,  0,  0, 20, 20],
                [20, 30, 10,  0,  0, 10, 30, 20]
            ]),
            "King_endgame": np.array([
                [-50,-40,-30,-20,-20,-30,-40,-50],
                [-30,-20,-10,  0,  0,-10,-20,-30],
                [-30,-10, 20, 30, 30, 20,-10,-30],
                [-30,-10, 30, 40, 40, 30,-10,-30],
                [-30,-10, 30, 40, 40, 30,-10,-30],
                [-30,-10, 20, 30, 30, 20,-10,-30],
                [-30,-30,  0,  0,  0,  0,-30,-30],
                [-50,-30,-30,-30,-30,-30,-30,-50]
            ])
        }
        
        # Pré-calculer les tables inversées pour les pions noirs
        self.position_tables["Pawn_black"] = np.flipud(self.position_tables["Pawn"])
        
        # Initialiser la table de transposition
        self.transposition_table = {}
        
        # Initialiser la base de données d'ouvertures avec pandas
        self.opening_book = self.load_opening_book()
        
        # Initialiser la base de données d'apprentissage
        self.learning_data = self.load_learning_data()
        
        # Historique des parties pour l'apprentissage
        self.game_history = []
        
        # Nombre de nœuds évalués (pour les statistiques)
        self.nodes_evaluated = 0
        self.evaluation_times = []
        self.move_times = []
        
        # Journal des chemins de pensée
        self.thought_log = []
        self.max_log_entries = 100  # Limiter le nombre d'entrées pour éviter une utilisation excessive de la mémoire
        
        # Nombre de threads pour le parallélisme
        self.max_workers = 4
        
    def set_color(self, color):
        """Définit la couleur de l'IA."""
        self.color = color
        
    def set_difficulty(self, difficulty):
        """Définit la difficulté de l'IA."""
        self.difficulty = difficulty

    def get_best_move(self, board, max_time=5):
        """Sélectionne le meilleur mouvement en fonction de la difficulté.
        
        Args:
            board: Le plateau de jeu actuel
            max_time: Le temps maximum de réflexion en secondes (par défaut: 5 secondes)
        """
        start_time = time.time()
        
        # Réinitialiser les statistiques et le journal de pensées
        self.nodes_evaluated = 0
        
        # Vérifier si l'attribut thought_log existe, sinon l'initialiser
        if not hasattr(self, 'thought_log'):
            self.thought_log = []
        else:
            self.thought_log = []
        
        # Ajouter une entrée au journal
        self.log_thought("Début de la recherche du meilleur coup pour les " + self.color)
        self.log_thought(f"Temps maximum de réflexion: {max_time} secondes")
        
        # Obtenir tous les coups valides immédiatement comme solution de secours
        all_valid_moves = self.get_all_valid_moves(board, self.color)
        if not all_valid_moves:
            self.log_thought("Aucun coup valide trouvé!")
            return None
            
        # Sélectionner un coup par défaut au cas où le temps serait dépassé
        default_move = random.choice(all_valid_moves)
        
        # Vérifier si nous sommes dans l'ouverture (avec un timeout)
        try:
            # Limiter le temps pour trouver un coup d'ouverture à 10% du temps total
            opening_timeout = min(0.5, max_time * 0.1)  # Maximum 0.5 secondes
            opening_move = self.get_opening_move(board)
            
            # Si un coup d'ouverture est trouvé, le jouer
            if opening_move:
                self.log_thought("Coup d'ouverture trouvé dans la base de données")
                start_pos, end_pos = opening_move
                start_notation = chr(start_pos[1] + ord('a')) + str(8 - start_pos[0])
                end_notation = chr(end_pos[1] + ord('a')) + str(8 - end_pos[0])
                self.log_thought(f"Joue le coup d'ouverture: {start_notation} → {end_notation}")
                return opening_move
        except Exception as e:
            pass  # Add a placeholder statement to handle the exception
            self.log_thought(f"Erreur lors de la recherche d'un coup d'ouverture: {str(e)}")
        
        # Vérifier si le temps est presque écoulé
        if time.time() - start_time > max_time * 0.5:
            self.log_thought("Temps presque écoulé, utilisation d'un coup semi-aléatoire")
            move = self.get_smart_random_move(board)
            return move
            
        # Sinon, utiliser l'algorithme approprié selon la difficulté
        try:
            if self.difficulty == "easy":
                self.log_thought("Utilisation de l'algorithme de sélection semi-aléatoire (difficulté: facile)")
                move = self.get_smart_random_move(board)
            elif self.difficulty == "medium":
                self.log_thought("Utilisation de l'algorithme minimax avec profondeur 3 (difficulté: moyenne)")
                # Réduire le temps restant pour s'assurer de terminer à temps
                remaining_time = max(1, max_time - (time.time() - start_time))
                move = self.get_minimax_move(board, depth=3, max_time=remaining_time)
            else:  # hard
                # Augmenter la profondeur pour le niveau difficile
                depth = 8 if max_time >= 15 else 7 if max_time >= 10 else 6
                self.log_thought(f"Utilisation de l'algorithme minimax avec profondeur {depth} (difficulté: difficile)")
                self.log_thought(f"Temps de réflexion accordé: {max_time} secondes")
                # Réduire le temps restant pour s'assurer de terminer à temps
                remaining_time = max(1, max_time - (time.time() - start_time))
                move = self.get_minimax_move(board, depth=depth, max_time=remaining_time)
                
            # Si aucun coup n'a été trouvé, utiliser le coup par défaut
            if not move:
                self.log_thought("Aucun coup trouvé, utilisation du coup par défaut")
                move = default_move
                
            return move
        except Exception as e:
            # En cas d'erreur, utiliser le coup par défaut
            self.log_thought(f"Erreur lors de la recherche du meilleur coup: {str(e)}")
            return default_move
    
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
        """Cherche un mouvement dans la base de données d'ouvertures de manière optimisée."""
        # Vérification rapide avant de faire des calculs coûteux
        if not self.opening_book:
            self.log_thought("Base de données d'ouvertures vide")
            return None
            
        # Convertir le plateau en une représentation FEN simplifiée (utilise le cache)
        board_state = self.get_board_state(board)
        self.log_thought(f"État du plateau (FEN): {board_state}")
        
        # Vérifier si l'état du plateau est dans la base de données
        if board_state not in self.opening_book:
            self.log_thought(f"État du plateau non trouvé dans la base de données d'ouvertures")
            return None
            
        # Récupérer les mouvements possibles pour cet état
        moves = self.opening_book[board_state]
        if not moves:
            self.log_thought("Aucun mouvement trouvé pour cet état du plateau")
            return None
            
        # Optimisation: pré-calculer la liste des mouvements une seule fois
        move_list = list(moves.keys())
        if not move_list:
            self.log_thought("Liste de mouvements vide")
            return None
            
        self.log_thought(f"Mouvements d'ouverture disponibles: {move_list}")
        
        # Sélection rapide du mouvement
        if len(move_list) == 1 or random.random() < 0.9:  # 90% de chance ou un seul choix
            # Trouver le meilleur mouvement directement
            best_move = max(moves.items(), key=lambda x: x[1])[0]
            self.log_thought(f"Meilleur coup d'ouverture choisi: {best_move}")
            try:
                start_pos, end_pos = self.parse_move_notation(best_move)
                return (start_pos, end_pos)
            except Exception as e:
                self.log_thought(f"Erreur lors de la conversion du coup: {str(e)}")
                return None
        else:
            # Choisir un mouvement aléatoire
            move = random.choice(move_list)
            self.log_thought(f"Coup d'ouverture aléatoire choisi: {move}")
            try:
                start_pos, end_pos = self.parse_move_notation(move)
                return (start_pos, end_pos)
            except Exception as e:
                self.log_thought(f"Erreur lors de la conversion du coup: {str(e)}")
                return None
    
    @lru_cache(maxsize=256)  # Utiliser un cache pour éviter de recalculer les mêmes conversions
    def parse_move_notation(self, move_notation):
        """Convertit une notation de mouvement (ex: 'e2e4') en positions de départ et d'arrivée."""
        start_col = ord(move_notation[0]) - ord('a')
        start_row = 8 - int(move_notation[1])
        end_col = ord(move_notation[2]) - ord('a')
        end_row = 8 - int(move_notation[3])
        
        return ((start_row, start_col), (end_row, end_col))
    
    @lru_cache(maxsize=1024)  # Utiliser un cache pour éviter de recalculer les états de plateau déjà vus
    def get_board_state(self, board):
        """Convertit le plateau en une représentation FEN simplifiée."""
        try:
            # Utiliser des listes et join pour une meilleure performance
            rows = []
            for row in range(8):
                empty = 0
                row_str = []
                for col in range(8):
                    piece = board.get_piece(row, col)
                    if piece == "":
                        empty += 1
                    else:
                        if empty > 0:
                            row_str.append(str(empty))
                            empty = 0
                        # Vérifier si piece est un objet ou une chaîne
                        if hasattr(piece, '__class__') and hasattr(piece, 'color'):
                            piece_type = piece.__class__.__name__[0]
                            if piece.color == "white":
                                row_str.append(piece_type.upper())
                            else:
                                row_str.append(piece_type.lower())
                        else:
                            # Si piece n'est pas un objet valide, utiliser un caractère générique
                            row_str.append('?')
                if empty > 0:
                    row_str.append(str(empty))
                rows.append(''.join(row_str))
            
            # Ajouter le tour actuel
            turn = "w" if hasattr(board, 'turn') and board.turn == "white" else "b"
            fen = '/'.join(rows) + " " + turn
            
            return fen
        except Exception as e:
            # En cas d'erreur, retourner une chaîne qui ne sera pas dans la base de données
            self.log_thought(f"Erreur lors de la conversion du plateau en FEN: {str(e)}")
            return "error"
    
    def get_minimax_move(self, board, depth=5, max_time=10):
        """Utilise l'algorithme minimax avec élagage alpha-beta, table de transposition, 
        approfondissement itératif et parallélisme pour trouver le meilleur mouvement.
        
        Args:
            board: Le plateau de jeu actuel
            depth: La profondeur maximale de recherche
            max_time: Le temps maximum de réflexion en secondes (par défaut: 10 secondes)
        """
        start_time = time.time()
        
        # Réinitialiser la table de transposition pour cette recherche
        self.transposition_table = {}
        
        all_moves = self.get_all_valid_moves(board, self.color)
        if not all_moves:
            return None
            
        # Trier les mouvements pour améliorer l'élagage alpha-beta
        sorted_moves = self.order_moves(board, all_moves)
        
        # Sélectionner un coup par défaut au cas où le temps serait dépassé
        default_move = sorted_moves[0] if sorted_moves else None
        
        # Évaluer rapidement les premiers coups pour avoir une solution de secours
        self.log_thought("Évaluation rapide des premiers coups...")
        quick_results = []
        for i, move in enumerate(sorted_moves[:min(5, len(sorted_moves))]):
            start_pos, end_pos = move
            temp_board = board.copy()
            piece = temp_board.get_piece(start_pos[0], start_pos[1])
            temp_board.set_piece(end_pos[0], end_pos[1], piece)
            temp_board.set_piece(start_pos[0], start_pos[1], "")
            
            # Évaluation simple
            score = self.evaluate_board(temp_board)
            is_safe = self.is_move_safe(board, temp_board, start_pos, end_pos, piece)
            quick_results.append((score, move, is_safe))
            
            # Si nous avons au moins un coup évalué et que le temps commence à être long, on s'arrête
            if i > 0 and time.time() - start_time > max_time * 0.15:
                self.log_thought(f"Évaluation rapide terminée après {i+1} coups (temps limite)")
                break
        
        # Trouver le meilleur coup rapide comme solution de secours
        best_quick_score = -float('inf')
        best_quick_move = default_move
        safe_moves = []  # Initialiser la liste des coups sûrs
        for score, move, is_safe in quick_results:
            if score > best_quick_score:
                best_quick_score = score
                best_quick_move = move
        
            if is_safe:
                safe_moves.append((score, move))
                
        # Approfondissement itératif: commencer par une profondeur faible et augmenter progressivement
        best_move_so_far = best_quick_move
        best_score_so_far = best_quick_score
        
        # Commencer à une profondeur de 2 et augmenter jusqu'à la profondeur maximale
        for current_depth in range(2, depth + 1):
            # Vérifier si nous avons encore assez de temps
            elapsed_time = time.time() - start_time
            if elapsed_time > max_time * 0.8:
                self.log_thought(f"Temps presque écoulé ({elapsed_time:.2f}s), arrêt à la profondeur {current_depth-1}")
                break
                
            self.log_thought(f"Analyse à la profondeur {current_depth}...")
            
            # Réinitialiser les résultats pour cette profondeur
            depth_results = []
        
            # Utiliser le parallélisme pour évaluer les mouvements en parallèle à cette profondeur
            try:
                if len(sorted_moves) > 1 and current_depth >= 3:
                    self.log_thought(f"Évaluation parallèle de {len(sorted_moves)} coups à la profondeur {current_depth}")
                    
                    # Calculer le temps restant pour cette profondeur
                    remaining_time = max_time * 0.8 - (time.time() - start_time)
                    time_per_depth = remaining_time / (depth - current_depth + 1)
                    depth_timeout = min(time_per_depth, max_time * 0.3)  # Ne pas utiliser plus de 30% du temps total
                    
                    # Utiliser ThreadPoolExecutor avec un timeout
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        future_to_move = {executor.submit(self._evaluate_single_move, board, move, current_depth, start_time, depth_timeout): move for move in sorted_moves}
                        
                        # Collecter les résultats au fur et à mesure qu'ils sont disponibles
                        for future in ThreadPoolExecutor().map(lambda f: f, future_to_move.keys(), timeout=depth_timeout):
                            try:
                                result = future.result(timeout=0.1)  # Petit timeout pour vérifier si le résultat est prêt
                                depth_results.append(result)
                                
                                # Si le temps est presque écoulé, on s'arrête
                                if time.time() - start_time > max_time * 0.8:
                                    self.log_thought(f"Temps presque écoulé, arrêt de l'évaluation à la profondeur {current_depth}")
                                    break
                            except Exception as e:
                                # Si une exception se produit, on continue avec les autres coups
                                continue
                else:
                    self.log_thought(f"Évaluation séquentielle de {len(sorted_moves)} coups à la profondeur {current_depth}")
                    
                    # Évaluer les coups séquentiellement avec vérification du temps
                    for i, move in enumerate(sorted_moves):
                        # Vérifier si le temps est presque écoulé
                        if time.time() - start_time > max_time * 0.8:
                            self.log_thought(f"Temps presque écoulé, arrêt de l'évaluation à la profondeur {current_depth}")
                            break
                        
                        result = self._evaluate_single_move(board, move, current_depth, start_time, max_time * 0.2)
                        depth_results.append(result)
                
                # Mettre à jour le meilleur coup pour cette profondeur
                if depth_results:
                    best_depth_score = -float('inf')
                    best_depth_move = best_move_so_far
                    
                    for score, move, is_safe in depth_results:
                        if score > best_depth_score:
                            best_depth_score = score
                            best_depth_move = move
                    
                    # Mettre à jour le meilleur coup global
                    best_move_so_far = best_depth_move
                    best_score_so_far = best_depth_score
                    self.log_thought(f"Meilleur coup à la profondeur {current_depth}: {best_depth_move} (score: {best_depth_score:.1f})")
                
            except Exception as e:
                # En cas d'erreur, continuer avec la profondeur suivante
                self.log_thought(f"Erreur à la profondeur {current_depth}: {str(e)}")
                continue
        
        # Utiliser le meilleur coup trouvé ou le coup rapide si aucun résultat
        if best_move_so_far:
            self.log_thought(f"Meilleur coup final: {best_move_so_far} (score: {best_score_so_far:.1f})")
            results = depth_results if depth_results else quick_results
        else:
            self.log_thought("Aucun résultat obtenu, utilisation des résultats rapides")
            results = quick_results
        
        # Trouver le meilleur coup et les coups sûrs parmi tous les résultats
        best_score = best_score_so_far
        best_move = best_move_so_far  # Utiliser le meilleur coup trouvé par l'approfondissement itératif
        # Ne pas réinitialiser safe_moves car nous l'avons déjà initialisé plus haut
        
        # Parcourir tous les résultats pour trouver les coups sûrs
        for score, move, is_safe in results:
            if is_safe:
                safe_moves.append((score, move))
            
            # Mettre à jour le meilleur coup si nécessaire
            if score > best_score:
                best_score = score
                best_move = move
                
        # Si nous avons des coups sûrs, choisir le meilleur parmi eux
        if safe_moves:
            safe_moves.sort(reverse=True)  # Trier par score décroissant
            best_safe_score, best_safe_move = safe_moves[0]
            
            # Si le meilleur coup sûr n'est pas trop inférieur au meilleur coup global, le préférer
            if best_safe_score > best_score - 150:  # Tolérance réduite à 150 points pour favoriser les coups sûrs
                self.log_thought(f"Choix d'un coup plus sûr: {best_safe_score:.1f} vs {best_score:.1f}")
                best_move = best_safe_move
                best_score = best_safe_score
        
        # Enregistrer le mouvement dans l'historique pour l'apprentissage
        if best_move:
            self.record_move(board, best_move, best_score)
        
        # Enregistrer le temps de calcul
        end_time = time.time()
        total_time = end_time - start_time
        self.move_times.append(total_time)
        
        # Afficher des statistiques détaillées
        self.log_thought(f"Temps total de réflexion: {total_time:.2f} secondes")
        self.log_thought(f"Nombre de nœuds évalués: {self.nodes_evaluated}")
        self.log_thought(f"Profondeur maximale atteinte: {depth}")
        self.log_thought(f"Score du meilleur coup: {best_score:.1f}")
        
        self.log_thought(f"Temps total de réflexion: {total_time:.2f} secondes")
        
        # Générer un graphique de performance si nous avons assez de données
        if len(self.move_times) >= 5:
            self._generate_performance_chart()
        
        return best_move
    
    def _evaluate_single_move(self, board, move, depth, start_time=None, max_time=None):
        """Évalue un seul mouvement avec une limite de temps optionnelle."""
        start_pos, end_pos = move
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
        alpha = -float('inf')
        beta = float('inf')
        
        # Passer les paramètres de temps à minimax
        score = -self.minimax(temp_board, depth-1, -beta, -alpha, False, start_time, max_time)
        
        return (score, move, is_safe)
    
    def _evaluate_moves_parallel(self, board, moves, depth, start_time=None, max_time=None):
        """Évalue les mouvements en parallèle pour améliorer les performances."""
        results = []
        
        # Utiliser ThreadPoolExecutor pour le parallélisme
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._evaluate_single_move, board, move, depth, start_time, max_time) for move in moves]
            for future in futures:
                try:
                    # Vérifier si le temps est presque écoulé
                    if start_time and max_time and time.time() - start_time > max_time * 0.9:
                        break
                    
                    # Utiliser un petit timeout pour éviter de bloquer
                    result = future.result(timeout=0.5)
                    results.append(result)
                except Exception as e:
                    # En cas d'erreur, continuer avec les autres coups
                    continue
        
        return results
    
    def _evaluate_moves_sequential(self, board, moves, depth, start_time=None, max_time=None):
        """Évalue les mouvements séquentiellement avec une limite de temps optionnelle."""
        results = []
        alpha = -float('inf')
        beta = float('inf')
        
        for move in moves:
            # Vérifier si le temps est presque écoulé
            if start_time and max_time and time.time() - start_time > max_time * 0.9:
                self.log_thought(f"Temps presque écoulé, arrêt de l'évaluation séquentielle après {len(results)} coups")
                break
                
            start_pos, end_pos = move
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
            score = -self.minimax(temp_board, depth-1, -beta, -alpha, False, start_time, max_time)
            
            results.append((score, move, is_safe))
            alpha = max(alpha, score)
        
        return results
        
    def _generate_performance_chart(self):
        """Génère un graphique de performance pour analyser l'IA."""
        try:
            # Créer un dossier pour les graphiques s'il n'existe pas
            charts_dir = os.path.join(os.path.dirname(__file__), 'charts')
            os.makedirs(charts_dir, exist_ok=True)
            
            # Créer un DataFrame pandas pour l'analyse
            performance_data = pd.DataFrame({
                'Move': range(1, len(self.move_times) + 1),
                'Move Time (s)': self.move_times,
                'Evaluation Time (ms)': [t * 1000 for t in self.evaluation_times[-len(self.move_times):]]
            })
            
            # Vérifier si nous sommes dans le thread principal
            if not is_main_thread:
                self.log_thought("Génération de graphique désactivée dans les threads non principaux")
                return
                
            # Créer un graphique avec matplotlib
            plt.figure(figsize=(12, 8))
            
            # Graphique du temps de calcul des coups
            plt.subplot(2, 1, 1)
            plt.plot(performance_data['Move'], performance_data['Move Time (s)'], 'b-', marker='o')
            plt.title('Temps de calcul des coups')
            plt.xlabel('Numéro du coup')
            plt.ylabel('Temps (secondes)')
            plt.grid(True)
            
            # Sauvegarder les données brutes en CSV (toujours sûr, même dans les threads non principaux)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = os.path.join(charts_dir, f'performance_data_{timestamp}.csv')
            performance_data.to_csv(csv_path, index=False)
            
            self.log_thought(f"Données de performance sauvegardées: {csv_path}")
            self.log_thought(f"Temps moyen de calcul: {performance_data['Move Time (s)'].mean():.2f} secondes")
            
            # Ne générer le graphique que dans le thread principal
            if is_main_thread:
                # Graphique du temps d'évaluation moyen
                plt.subplot(2, 1, 2)
                plt.plot(performance_data['Move'], performance_data['Evaluation Time (ms)'], 'r-', marker='x')
                plt.title('Temps d\'évaluation moyen')
                plt.xlabel('Numéro du coup')
                plt.ylabel('Temps (millisecondes)')
                plt.grid(True)
                
            plt.tight_layout()
                
                # Sauvegarder le graphique
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_path = os.path.join(charts_dir, f'performance_{timestamp}.png')
            plt.savefig(chart_path)
            if 'Evaluation Time (ms)' in performance_data and not performance_data['Evaluation Time (ms)'].empty:
                plt.close()    
                self.log_thought(f"Graphique de performance généré: {chart_path}")
        except Exception as e:
            self.log_thought(f"Erreur lors de la génération du graphique: {e}")
                # Ne pas afficher l'erreur dans la console pour éviter de polluer les logs
        
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
        
        # Déterminer si nous sommes en début de partie
        piece_count = 0
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, 'color'):
                    piece_count += 1
        
        early_game = piece_count >= 28  # Considérer comme début de partie si plus de 28 pièces
        
        # Définir les cases centrales et le centre étendu
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        extended_center = [(2, 2), (2, 3), (2, 4), (2, 5), 
                          (3, 2), (3, 5), 
                          (4, 2), (4, 5), 
                          (5, 2), (5, 3), (5, 4), (5, 5)]
        
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
            
            # Priorité aux mouvements vers le centre en début de partie
            if early_game:
                # Bonus important pour les mouvements vers le centre
                if (end_row, end_col) in center_squares:
                    score += 200
                # Bonus modéré pour les mouvements vers le centre étendu
                elif (end_row, end_col) in extended_center:
                    score += 100
                
                # Bonus pour le développement des pièces en début de partie
                piece = board.get_piece(start_row, start_col)
                if piece and hasattr(piece, '__class__'):
                    piece_type = piece.__class__.__name__
                    # Encourager le développement des cavaliers et fous
                    if piece_type in ["Knight", "Bishop"]:
                        # Si la pièce est sur sa position initiale
                        if (piece.color == "white" and start_row == 7) or (piece.color == "black" and start_row == 0):
                            score += 80  # Bonus pour sortir les pièces
            
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
        # Vérifier si l'attribut thought_log existe, sinon l'initialiser
        if not hasattr(self, 'thought_log'):
            self.thought_log = []
            self.max_log_entries = 20  # Réduire le nombre maximum d'entrées pour améliorer les performances
            
        # Ajouter un horodatage
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Ajouter l'entrée au journal
        self.thought_log.append(f"[{timestamp}] {thought}")
        
        # Limiter la taille du journal
        if not hasattr(self, 'max_log_entries'):
            self.max_log_entries = 20  # Réduire le nombre maximum d'entrées
            
        if len(self.thought_log) > self.max_log_entries:
            self.thought_log.pop(0)
    
    def minimax(self, board, depth, alpha, beta, is_maximizing, start_time=None, max_time=None):
        """Implémentation de l'algorithme minimax avec élagage alpha-beta et table de transposition."""
        # Vérifier si le temps est écoulé
        if start_time and max_time and time.time() - start_time > max_time * 0.95:
            # Si le temps est presque écoulé, retourner une évaluation rapide
            return self.evaluate_board(board) if is_maximizing else -self.evaluate_board(board)
            
        # Incrémenter le compteur de nœuds
        self.nodes_evaluated += 1
        
        # Enregistrer la pensée seulement pour les niveaux les plus élevés (pour réduire drastiquement les logs)
        if depth >= 5:  # Augmenter le seuil pour réduire le nombre de logs
            player = self.color if is_maximizing else ("white" if self.color == "black" else "black")
            # Simplifier le message pour réduire la taille des logs
            self.log_thought(f"Analyse profondeur {depth}, {player}")
        
        # Vérifier la table de transposition
        board_hash = self.hash_board(board)
        if board_hash in self.transposition_table:
            stored_depth, stored_score, stored_flag = self.transposition_table[board_hash]
            if stored_depth >= depth:
                if stored_flag == 'exact':
                    if depth >= 5:  # Augmenter le seuil pour réduire les logs
                        self.log_thought(f"Position trouvée dans table, score: {stored_score:.1f}")
                    return stored_score
                elif stored_flag == 'lowerbound' and stored_score > alpha:
                    alpha = stored_score
                    if depth >= 5:  # Augmenter le seuil
                        self.log_thought(f"Borne inf: {alpha:.1f}")
                elif stored_flag == 'upperbound' and stored_score < beta:
                    beta = stored_score
                    if depth >= 5:  # Augmenter le seuil
                        self.log_thought(f"Borne sup: {beta:.1f}")
                
                if alpha >= beta:
                    if depth >= 5:  # Augmenter le seuil
                        self.log_thought(f"Coupure α-β: {stored_score:.1f}")
                    return stored_score
        
        # Vérifier les conditions de terminaison
        if depth == 0:
            score = self.quiescence_search(board, alpha, beta, is_maximizing, 3, start_time, max_time)
            if depth >= 5:  # Augmenter le seuil
                self.log_thought(f"Quiescence: {score:.1f}")
            return score
        
        # Vérifier si le jeu est terminé
        game_status = board.check_game_status()
        if game_status != "In Progress":
            if game_status == "Checkmate":
                score = -20000 if is_maximizing else 20000
                if depth >= 5:  # Augmenter le seuil
                    self.log_thought(f"Échec et mat: {score}")
                return score
            else:  # Stalemate
                if depth >= 5:  # Augmenter le seuil
                    self.log_thought("Pat: 0")
                return 0
        
        # Récupérer les mouvements valides
        color = self.color if is_maximizing else ("white" if self.color == "black" else "black")
        all_moves = self.get_all_valid_moves(board, color)
        
        # Trier les mouvements pour améliorer l'élagage
        sorted_moves = self.order_moves(board, all_moves)
        
        if depth >= 5:  # Augmenter le seuil
            self.log_thought(f"Coups: {len(sorted_moves)}")
        
        if is_maximizing:
            max_score = -float('inf')
            best_move = None
            
            for start_pos, end_pos in sorted_moves:
                # Suppression du log d'évaluation de chaque coup pour améliorer les performances
                
                # Simuler le mouvement
                temp_board = board.copy()
                start_row, start_col = start_pos
                end_row, end_col = end_pos
                
                # Exécuter le mouvement sur le plateau temporaire
                piece = temp_board.get_piece(start_row, start_col)
                temp_board.set_piece(end_row, end_col, piece)
                temp_board.set_piece(start_row, start_col, "")
                
                score = self.minimax(temp_board, depth-1, alpha, beta, False, start_time, max_time)
                
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
                
                score = self.minimax(temp_board, depth-1, alpha, beta, True, start_time, max_time)
                
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
    
    def quiescence_search(self, board, alpha, beta, is_maximizing, depth=3, start_time=None, max_time=None):
        """Recherche de quiescence pour éviter l'effet d'horizon."""
        # Vérifier si le temps est écoulé
        if start_time and max_time and time.time() - start_time > max_time * 0.95:
            # Si le temps est presque écoulé, retourner une évaluation rapide
            return self.evaluate_board(board)
            
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
                
                score = self.quiescence_search(temp_board, alpha, beta, False, depth-1, start_time, max_time)
                
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
                
                score = self.quiescence_search(temp_board, alpha, beta, True, depth-1, start_time, max_time)
                
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
    
    @lru_cache(maxsize=1024)
    def evaluate_board(self, board):
        """Évalue la position actuelle du plateau avec une fonction d'évaluation avancée optimisée avec numpy."""
        start_time = time.time()
        
        if board.check_game_status() == "Checkmate":
            # Si c'est échec et mat, retourner une valeur extrême
            if board.turn == self.color:
                return -20000  # Nous avons perdu
            else:
                return 20000   # Nous avons gagné
        
        if board.check_game_status() == "Stalemate":
            return 0  # Match nul
        
        # Créer une représentation matricielle du plateau pour accélérer les calculs
        board_matrix = self._create_board_matrix(board)
        
        # Initialiser le score
        score = 0
        piece_count = {"white": 0, "black": 0}
        
        # Calculer les pièces attaquées et défendues
        attacked_pieces = self.get_attacked_pieces(board)
        defended_pieces = self.get_defended_pieces(board)
        
        # Évaluer la valeur matérielle et positionnelle avec numpy
        piece_positions = {}
        
        # Collecter les positions des pièces par type et couleur
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, 'color'):
                    piece_type = piece.__class__.__name__
                    piece_count[piece.color] += 1
                    
                    key = f"{piece_type}_{piece.color}"
                    if key not in piece_positions:
                        piece_positions[key] = []
                    piece_positions[key].append((row, col))
        
        # Calculer les scores matériels et positionnels en une seule passe
        for key, positions in piece_positions.items():
            piece_type, color = key.split('_')
            piece_value = self.piece_values.get(piece_type, 0)
            
            # Valeur matérielle
            if color == self.color:
                score += piece_value * len(positions)
            else:
                score -= piece_value * len(positions)
            
            # Valeur positionnelle
            for row, col in positions:
                # Sélectionner la table de position appropriée
                if piece_type == "Pawn" and color == "black":
                    position_value = self.position_tables["Pawn_black"][row, col]
                else:
                    position_table = self.position_tables.get(piece_type, np.zeros((8, 8)))
                    position_value = position_table[row, col]
                
                # Ajuster le score en fonction de la couleur
                if color == self.color:
                    score += position_value * 0.1
                else:
                    score -= position_value * 0.1
        
        # Déterminer si nous sommes en fin de partie
        is_endgame = (piece_count["white"] + piece_count["black"] <= 10)
        
        # Bonus pour la mobilité (nombre de mouvements possibles) - utiliser numpy pour accélérer
        my_moves = len(self.get_all_valid_moves(board, self.color))
        opponent_color = "white" if self.color == "black" else "black"
        opponent_moves = len(self.get_all_valid_moves(board, opponent_color))
        mobility_score = 0.1 * (my_moves - opponent_moves)
        score += mobility_score
        
        # Bonus pour le contrôle du centre - utiliser numpy pour accélérer
        # Augmenter significativement la valeur du contrôle du centre
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        extended_center = [(2, 2), (2, 3), (2, 4), (2, 5), 
                          (3, 2), (3, 5), 
                          (4, 2), (4, 5), 
                          (5, 2), (5, 3), (5, 4), (5, 5)]
        
        # Contrôle direct du centre (occupation)
        center_control = 0
        for row, col in center_squares:
            piece = board.get_piece(row, col)
            if piece and hasattr(piece, 'color'):
                if piece.color == self.color:
                    center_control += 1
                else:
                    center_control -= 1
        
        # Contrôle étendu du centre (pièces qui attaquent le centre)
        extended_control = 0
        for row, col in extended_center:
            piece = board.get_piece(row, col)
            if piece and hasattr(piece, 'color'):
                if piece.color == self.color:
                    extended_control += 0.5
                else:
                    extended_control -= 0.5
        
        # Donner plus d'importance au contrôle du centre en début de partie
        center_importance = 50 if piece_count["white"] + piece_count["black"] >= 28 else 30
        
        score += center_control * center_importance
        score += extended_control * (center_importance / 2)
        
        # Pénalité pour les pions doublés - utiliser numpy pour accélérer
        doubled_pawns_score = 0
        for col in range(8):
            # Compter les pions par colonne avec numpy
            white_pawns = sum(1 for row in range(8) if board.get_piece(row, col) and 
                             hasattr(board.get_piece(row, col), '__class__') and 
                             board.get_piece(row, col).__class__.__name__ == 'Pawn' and 
                             board.get_piece(row, col).color == "white")
            
            black_pawns = sum(1 for row in range(8) if board.get_piece(row, col) and 
                             hasattr(board.get_piece(row, col), '__class__') and 
                             board.get_piece(row, col).__class__.__name__ == 'Pawn' and 
                             board.get_piece(row, col).color == "black")
            
            # Pénaliser les pions doublés
            if white_pawns > 1:
                if self.color == "white":
                    doubled_pawns_score -= (white_pawns - 1) * 20
                else:
                    doubled_pawns_score += (white_pawns - 1) * 20
            
            if black_pawns > 1:
                if self.color == "black":
                    doubled_pawns_score -= (black_pawns - 1) * 20
                else:
                    doubled_pawns_score += (black_pawns - 1) * 20
        
        score += doubled_pawns_score
        
        # Bonus pour les pions passés - optimisé
        passed_pawns_score = 0
        
        # Créer des masques pour les pions blancs et noirs
        white_pawn_mask = np.zeros((8, 8), dtype=bool)
        black_pawn_mask = np.zeros((8, 8), dtype=bool)
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, '__class__') and piece.__class__.__name__ == 'Pawn':
                    if piece.color == "white":
                        white_pawn_mask[row, col] = True
                    else:
                        black_pawn_mask[row, col] = True
        
        # Vérifier les pions passés
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, '__class__') and piece.__class__.__name__ == 'Pawn':
                    is_passed = True
                    
                    # Vérifier s'il y a des pions adverses qui peuvent bloquer
                    if piece.color == "white":
                        # Vérifier devant le pion blanc
                        for r in range(row-1, -1, -1):
                            for c in range(max(0, col-1), min(8, col+2)):
                                if black_pawn_mask[r, c]:
                                    is_passed = False
                                    break
                    else:  # piece.color == "black"
                        # Vérifier devant le pion noir
                        for r in range(row+1, 8):
                            for c in range(max(0, col-1), min(8, col+2)):
                                if white_pawn_mask[r, c]:
                                    is_passed = False
                                    break
                    
                    if is_passed:
                        # Bonus pour les pions passés, plus important en fin de partie
                        if piece.color == self.color:
                            # Plus le pion est avancé, plus le bonus est important
                            rank_bonus = 7 - row if piece.color == "white" else row
                            passed_pawns_score += (20 + rank_bonus * 10) * (2 if is_endgame else 1)
                        else:
                            rank_bonus = 7 - row if piece.color == "white" else row
                            passed_pawns_score -= (20 + rank_bonus * 10) * (2 if is_endgame else 1)
        
        score += passed_pawns_score
        
        # Bonus pour la sécurité du roi - optimisé
        king_safety_score = 0
        
        for color in ["white", "black"]:
            king_pos = board.find_king(color)
            if king_pos:
                king_row, king_col = king_pos
                
                # Pénalité pour le roi exposé
                if is_endgame:
                    # En fin de partie, le roi doit être actif
                    # Distance au centre calculée avec numpy
                    center_distance = abs(3.5 - king_row) + abs(3.5 - king_col)
                    if color == self.color:
                        king_safety_score -= center_distance * 10
                    else:
                        king_safety_score += center_distance * 10
                else:
                    # En milieu de partie, le roi doit être protégé
                    # Créer un masque 3x3 autour du roi
                    king_area = np.zeros((3, 3), dtype=bool)
                    for dr in range(3):
                        for dc in range(3):
                            r, c = king_row + dr - 1, king_col + dc - 1
                            if 0 <= r < 8 and 0 <= c < 8:
                                piece = board.get_piece(r, c)
                                if piece and hasattr(piece, 'color') and piece.color == color:
                                    king_area[dr, dc] = True
                    
                    # Compter les pièces amies autour du roi (exclure le roi lui-même)
                    king_safety = np.sum(king_area) - 1  # -1 pour exclure le roi
                    
                    if color == self.color:
                        king_safety_score += king_safety * 10
                    else:
                        king_safety_score -= king_safety * 10
        
        score += king_safety_score
        
        # Vérifier si le roi est en échec
        check_score = 0
        if board.is_king_in_check(self.color):
            check_score -= 50  # Pénalité pour être en échec
        
        if board.is_king_in_check(opponent_color):
            check_score += 50  # Bonus pour mettre l'adversaire en échec
        
        score += check_score
        
        # Pénaliser les pièces attaquées et non défendues - optimisé
        exchange_score = 0
        for (row, col), attackers in attacked_pieces.items():
            piece = board.get_piece(row, col)
            if piece and hasattr(piece, '__class__'):
                piece_type = piece.__class__.__name__
                piece_value = self.piece_values.get(piece_type, 0)
                
                # Vérifier si la pièce est défendue
                is_defended = (row, col) in defended_pieces
                
                # Pénalité plus forte pour les pièces non défendues
                if not is_defended:
                    exchange_score -= piece_value * 0.3  # Pénalité sévère pour les pièces en danger
                    self.log_thought(f"Pièce en danger non défendue: {piece_type} en {chr(col + ord('a'))}{8-row}")
                else:
                    # Évaluer l'échange
                    attacker_values = [self.piece_values.get(board.get_piece(r, c).__class__.__name__, 0) 
                                      for r, c in attackers 
                                      if board.get_piece(r, c) and hasattr(board.get_piece(r, c), '__class__')]
                    
                    if attacker_values:
                        lowest_attacker_value = min(attacker_values)
                        
                        # Si l'échange est défavorable
                        if lowest_attacker_value < piece_value:
                            exchange_score -= (piece_value - lowest_attacker_value) * 0.2
                            self.log_thought(f"Échange défavorable possible: {piece_type} contre {lowest_attacker_value}")
        
        score += exchange_score
        
        # Enregistrer le temps d'évaluation
        end_time = time.time()
        self.evaluation_times.append(end_time - start_time)
        
        return score
        
    def _create_board_matrix(self, board):
        """Crée une représentation matricielle du plateau pour les calculs numpy."""
        # Créer une matrice 8x8x12 (8x8 cases, 12 canaux pour les différents types de pièces)
        # 6 types de pièces * 2 couleurs = 12 canaux
        matrix = np.zeros((8, 8, 12), dtype=np.int8)
        
        piece_types = ["Pawn", "Knight", "Bishop", "Rook", "Queen", "King"]
        colors = ["white", "black"]
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, '__class__'):
                    piece_type = piece.__class__.__name__
                    if piece_type in piece_types and hasattr(piece, 'color') and piece.color in colors:
                        type_idx = piece_types.index(piece_type)
                        color_idx = colors.index(piece.color)
                        channel_idx = type_idx + 6 * color_idx
                        matrix[row, col, channel_idx] = 1
        
        return matrix
    
    def get_all_valid_moves(self, board, color):
        """Récupère tous les mouvements valides pour une couleur donnée de manière optimisée."""
        all_moves = []
        
        # Optimisation : vérifier d'abord les pièces qui ont le plus de mouvements potentiels
        # Ordre de priorité : Dame, Tour, Fou, Cavalier, Roi, Pion
        piece_positions = []
        
        # Collecter toutes les positions des pièces de la couleur donnée
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and hasattr(piece, 'color') and piece.color == color:
                    piece_type = piece.__class__.__name__
                    # Attribuer une priorité à chaque type de pièce
                    priority = {
                        "Queen": 0,
                        "Rook": 1,
                        "Bishop": 2,
                        "Knight": 3,
                        "King": 4,
                        "Pawn": 5
                    }.get(piece_type, 6)
                    piece_positions.append((priority, row, col))
        
        # Trier les positions par priorité
        piece_positions.sort()
        
        # Limiter le nombre de mouvements à vérifier si le temps est critique
        max_pieces_to_check = len(piece_positions)
        
        # Récupérer les mouvements valides pour chaque pièce
        for _, row, col in piece_positions[:max_pieces_to_check]:
            try:
                valid_moves = board.get_valid_moves(row, col)
                for end_row, end_col in valid_moves:
                    all_moves.append(((row, col), (end_row, end_col)))
                    
                    # Si nous avons déjà trouvé beaucoup de mouvements, c'est suffisant
                    if len(all_moves) > 50:  # Limite arbitraire pour éviter de passer trop de temps
                        return all_moves
            except Exception as e:
                # En cas d'erreur, continuer avec les autres pièces
                continue
        
        # Si aucun mouvement n'a été trouvé, vérifier toutes les pièces sans optimisation
        if not all_moves:
            for row in range(8):
                for col in range(8):
                    piece = board.get_piece(row, col)
                    if piece and hasattr(piece, 'color') and piece.color == color:
                        try:
                            valid_moves = board.get_valid_moves(row, col)
                            for end_row, end_col in valid_moves:
                                all_moves.append(((row, col), (end_row, end_col)))
                        except Exception:
                            continue
        
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
        """Charge la base de données d'ouvertures de manière optimisée."""
        try:
            # Vérifier si le fichier CSV existe
            csv_path = os.path.join(os.path.dirname(__file__), 'opening_book.csv')
            if os.path.exists(csv_path):
                # Utiliser une méthode plus rapide pour charger les données
                opening_book = {}
                
                # Utiliser un dictionnaire pour stocker temporairement les données
                # Cette approche est plus rapide que d'utiliser pandas pour de petits fichiers
                with open(csv_path, 'r') as f:
                    # Ignorer l'en-tête
                    next(f)
                    for line in f:
                        try:
                            # Diviser la ligne en colonnes
                            parts = line.strip().split(',')
                            if len(parts) >= 3:
                                board_state = parts[0]
                                move = parts[1]
                                score = float(parts[2])
                                
                                # Ajouter au dictionnaire
                                if board_state not in opening_book:
                                    opening_book[board_state] = {}
                                
                                opening_book[board_state][move] = score
                        except Exception:
                            # Ignorer les lignes mal formatées
                            continue
                
                return opening_book
            
            # Si le fichier CSV n'existe pas, vérifier le fichier JSON (pour la compatibilité)
            json_path = os.path.join(os.path.dirname(__file__), 'opening_book.json')
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.load(f)
                
                # Convertir en CSV pour les prochaines utilisations
                self._convert_opening_book_to_csv(data)
                
                return data
            
            return {}
        except Exception as e:
            print(f"Erreur lors du chargement de la base de données d'ouvertures: {e}")
            return {}
    
    def _convert_opening_book_to_csv(self, opening_book):
        """Convertit la base de données d'ouvertures en CSV pour une meilleure performance."""
        try:
            # Créer une liste de dictionnaires pour pandas
            data = []
            for board_state, moves in opening_book.items():
                for move, score in moves.items():
                    data.append({
                        'board_state': board_state,
                        'move': move,
                        'score': score
                    })
            
            # Créer un DataFrame pandas
            df = pd.DataFrame(data)
            
            # Sauvegarder en CSV
            csv_path = os.path.join(os.path.dirname(__file__), 'opening_book.csv')
            df.to_csv(csv_path, index=False)
            
            self.log_thought(f"Base de données d'ouvertures convertie en CSV: {len(df)} entrées")
        except Exception as e:
            self.log_thought(f"Erreur lors de la conversion de la base de données d'ouvertures: {e}")
            print(f"Erreur lors de la conversion de la base de données d'ouvertures: {e}")
    
    def save_opening_book(self):
        """Sauvegarde la base de données d'ouvertures en utilisant pandas."""
        try:
            # Convertir le dictionnaire en DataFrame
            data = []
            for board_state, moves in self.opening_book.items():
                for move, score in moves.items():
                    data.append({
                        'board_state': board_state,
                        'move': move,
                        'score': score
                    })
            
            # Créer un DataFrame pandas
            df = pd.DataFrame(data)
            
            # Sauvegarder en CSV
            csv_path = os.path.join(os.path.dirname(__file__), 'opening_book.csv')
            df.to_csv(csv_path, index=False)
            
            self.log_thought(f"Base de données d'ouvertures sauvegardée: {len(df)} entrées")
        except Exception as e:
            self.log_thought(f"Erreur lors de la sauvegarde de la base de données d'ouvertures: {e}")
            print(f"Erreur lors de la sauvegarde de la base de données d'ouvertures: {e}")
    
    def load_learning_data(self):
        """Charge les données d'apprentissage en utilisant pandas."""
        try:
            # Vérifier si le fichier CSV existe
            csv_path = os.path.join(os.path.dirname(__file__), 'learning_data.csv')
            if os.path.exists(csv_path):
                # Charger avec pandas
                df = pd.read_csv(csv_path)
                
                # Convertir en dictionnaire
                learning_data = {}
                for _, row in df.iterrows():
                    move_key = row['move_key']
                    value = row['value']
                    learning_data[move_key] = value
                
                self.log_thought(f"Données d'apprentissage chargées: {len(df)} entrées")
                return learning_data
            
            # Si le fichier CSV n'existe pas, vérifier le fichier PKL (pour la compatibilité)
            pkl_path = os.path.join(os.path.dirname(__file__), 'learning_data.pkl')
            if os.path.exists(pkl_path):
                with open(pkl_path, 'rb') as f:
                    data = pickle.load(f)
                
                # Convertir en CSV pour les prochaines utilisations
                self._convert_learning_data_to_csv(data)
                
                return data
            
            return {}
        except Exception as e:
            self.log_thought(f"Erreur lors du chargement des données d'apprentissage: {e}")
            print(f"Erreur lors du chargement des données d'apprentissage: {e}")
            return {}
    
    def _convert_learning_data_to_csv(self, learning_data):
        """Convertit les données d'apprentissage en CSV pour une meilleure performance."""
        try:
            # Créer une liste de dictionnaires pour pandas
            data = []
            for move_key, value in learning_data.items():
                data.append({
                    'move_key': move_key,
                    'value': value
                })
            
            # Créer un DataFrame pandas
            df = pd.DataFrame(data)
            
            # Sauvegarder en CSV
            csv_path = os.path.join(os.path.dirname(__file__), 'learning_data.csv')
            df.to_csv(csv_path, index=False)
            
            self.log_thought(f"Données d'apprentissage converties en CSV: {len(df)} entrées")
        except Exception as e:
            self.log_thought(f"Erreur lors de la conversion des données d'apprentissage: {e}")
            print(f"Erreur lors de la conversion des données d'apprentissage: {e}")
    
    def save_learning_data(self):
        """Sauvegarde les données d'apprentissage en utilisant pandas."""
        try:
            # Convertir le dictionnaire en DataFrame
            data = []
            for move_key, value in self.learning_data.items():
                data.append({
                    'move_key': move_key,
                    'value': value
                })
            
            # Créer un DataFrame pandas
            df = pd.DataFrame(data)
            
            # Sauvegarder en CSV
            csv_path = os.path.join(os.path.dirname(__file__), 'learning_data.csv')
            df.to_csv(csv_path, index=False)
            
            self.log_thought(f"Données d'apprentissage sauvegardées: {len(df)} entrées")
        except Exception as e:
            self.log_thought(f"Erreur lors de la sauvegarde des données d'apprentissage: {e}")
            print(f"Erreur lors de la sauvegarde des données d'apprentissage: {e}")
            
    def get_thought_log(self):
        """Retourne le journal des chemins de pensée."""
        # Vérifier si l'attribut thought_log existe, sinon l'initialiser
        if not hasattr(self, 'thought_log'):
            self.thought_log = []
        
        # Limiter le nombre de logs retournés pour améliorer les performances
        # Ne retourner que les 10 derniers logs pour éviter de surcharger l'interface
        return self.thought_log[-10:] if len(self.thought_log) > 10 else self.thought_log
    
    def analyze_performance(self):
        """Analyse les performances de l'IA et génère des visualisations."""
        if not self.move_times or not self.evaluation_times:
            self.log_thought("Pas assez de données pour analyser les performances")
            return None
        
        try:
            # Créer un dossier pour les graphiques s'il n'existe pas
            charts_dir = os.path.join(os.path.dirname(__file__), 'charts')
            os.makedirs(charts_dir, exist_ok=True)
            
            # Vérifier si nous sommes dans le thread principal
            if not is_main_thread:
                self.log_thought("Analyse de performance désactivée dans les threads non principaux")
                return None
                
            # Créer un DataFrame pandas pour l'analyse
            performance_data = pd.DataFrame({
                'Move': range(1, len(self.move_times) + 1),
                'Move Time (s)': self.move_times,
                'Evaluation Time (ms)': [t * 1000 for t in self.evaluation_times[:len(self.move_times)] if t] if self.evaluation_times else [],
                'Nodes Evaluated': [self.nodes_evaluated / max(1, len(self.move_times))] * len(self.move_times)
            })
            
            # Statistiques descriptives
            stats = performance_data.describe()
            
            return {
                'stats_path': stats_path,
                'stats': stats
            }
            
        except Exception as e:
            self.log_thought(f"Erreur lors de l'analyse des performances: {e}")
            print(f"Erreur lors de l'analyse des performances: {e}")
            return None