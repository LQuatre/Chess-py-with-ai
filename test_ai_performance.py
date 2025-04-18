#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test de performance de l'IA d'échecs optimisée avec numpy, pandas et matplotlib.
Ce script compare les performances de l'IA avant et après optimisation.
"""

import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from game.board import Board
from game.ai import AI

def test_ai_performance(difficulty="medium", num_moves=5):
    """
    Teste les performances de l'IA en mesurant le temps de calcul pour plusieurs coups.
    
    Args:
        difficulty: Niveau de difficulté de l'IA ("easy", "medium", "hard")
        num_moves: Nombre de coups à calculer
    
    Returns:
        Un dictionnaire contenant les statistiques de performance
    """
    print(f"Test de performance de l'IA (difficulté: {difficulty})")
    print("=" * 50)
    
    # Initialiser le plateau et l'IA
    board = Board()
    ai = AI(color="black", difficulty=difficulty)
    
    # Statistiques
    move_times = []
    nodes_evaluated = []
    
    # Calculer plusieurs coups
    for i in range(num_moves):
        print(f"\nCalcul du coup {i+1}/{num_moves}...")
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        best_move = ai.get_best_move(board)
        end_time = time.time()
        
        # Enregistrer les statistiques
        move_time = end_time - start_time
        move_times.append(move_time)
        nodes_evaluated.append(ai.nodes_evaluated)
        
        print(f"Meilleur mouvement: {best_move}")
        print(f"Temps de calcul: {move_time:.2f} secondes")
        print(f"Nœuds évalués: {ai.nodes_evaluated}")
        
        # Exécuter le mouvement sur le plateau
        if best_move:
            start_pos, end_pos = best_move
            start_row, start_col = start_pos
            end_row, end_col = end_pos
            
            piece = board.get_piece(start_row, start_col)
            board.set_piece(end_row, end_col, piece)
            board.set_piece(start_row, start_col, "")
            
            # Changer le tour
            board.turn = "white" if board.turn == "black" else "black"
    
    # Calculer les statistiques
    stats = {
        "move_times": move_times,
        "nodes_evaluated": nodes_evaluated,
        "avg_move_time": np.mean(move_times),
        "max_move_time": np.max(move_times),
        "min_move_time": np.min(move_times),
        "std_move_time": np.std(move_times),
        "total_nodes": sum(nodes_evaluated),
        "avg_nodes": np.mean(nodes_evaluated)
    }
    
    # Afficher les statistiques
    print("\nStatistiques de performance:")
    print(f"Temps moyen de calcul: {stats['avg_move_time']:.2f} secondes")
    print(f"Temps maximum de calcul: {stats['max_move_time']:.2f} secondes")
    print(f"Temps minimum de calcul: {stats['min_move_time']:.2f} secondes")
    print(f"Écart-type des temps de calcul: {stats['std_move_time']:.2f} secondes")
    print(f"Nombre total de nœuds évalués: {stats['total_nodes']}")
    print(f"Nombre moyen de nœuds évalués par coup: {stats['avg_nodes']:.2f}")
    
    # Générer un graphique de performance
    generate_performance_chart(stats, difficulty)
    
    # Générer une analyse de performance avec l'IA
    ai.analyze_performance()
    
    return stats

def generate_performance_chart(stats, difficulty):
    """
    Génère un graphique de performance à partir des statistiques.
    
    Args:
        stats: Dictionnaire contenant les statistiques de performance
        difficulty: Niveau de difficulté de l'IA
    """
    # Créer un graphique avec matplotlib
    plt.figure(figsize=(12, 8))
    
    # Graphique du temps de calcul des coups
    plt.subplot(2, 1, 1)
    plt.plot(range(1, len(stats["move_times"]) + 1), stats["move_times"], 'b-', marker='o')
    plt.title(f'Temps de calcul des coups (difficulté: {difficulty})')
    plt.xlabel('Numéro du coup')
    plt.ylabel('Temps (secondes)')
    plt.grid(True)
    
    # Graphique du nombre de nœuds évalués
    plt.subplot(2, 1, 2)
    plt.plot(range(1, len(stats["nodes_evaluated"]) + 1), stats["nodes_evaluated"], 'r-', marker='x')
    plt.title('Nombre de nœuds évalués')
    plt.xlabel('Numéro du coup')
    plt.ylabel('Nœuds évalués')
    plt.grid(True)
    
    plt.tight_layout()
    
    # Sauvegarder le graphique
    import os
    charts_dir = os.path.join(os.path.dirname(__file__), 'game', 'charts')
    os.makedirs(charts_dir, exist_ok=True)
    
    chart_path = os.path.join(charts_dir, f'performance_test_{difficulty}.png')
    plt.savefig(chart_path)
    plt.close()
    
    print(f"\nGraphique de performance généré: {chart_path}")

if __name__ == "__main__":
    # Tester l'IA avec différents niveaux de difficulté
    for difficulty in ["easy", "medium", "hard"]:
        # Ajuster le nombre de coups en fonction de la difficulté
        num_moves = 10 if difficulty == "easy" else (5 if difficulty == "medium" else 3)
        
        stats = test_ai_performance(difficulty=difficulty, num_moves=num_moves)
        print("\n" + "=" * 50 + "\n")