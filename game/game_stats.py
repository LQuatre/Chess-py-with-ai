import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend which doesn't require a GUI
import matplotlib.pyplot as plt
import threading
import datetime
import json

# Vérifier si nous sommes dans le thread principal
is_main_thread = threading.current_thread() is threading.main_thread()

class GameStats:
    """Classe pour gérer les statistiques des parties d'échecs."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Retourne l'instance unique de GameStats (singleton)."""
        if cls._instance is None:
            cls._instance = GameStats()
        return cls._instance
    
    def __init__(self):
        """Initialise le gestionnaire de statistiques."""
        self.stats_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'game_stats.csv')
        self.charts_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'charts')
        
        # Créer les dossiers s'ils n'existent pas
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)
        
        # Charger les statistiques existantes ou créer un DataFrame vide
        if os.path.exists(self.stats_file):
            self.stats_df = pd.read_csv(self.stats_file)
        else:
            self.stats_df = pd.DataFrame(columns=[
                'game_id', 'date', 'game_type', 'white_player', 'black_player', 
                'winner', 'moves_count', 'duration', 'result', 'white_captured', 
                'black_captured', 'white_ai_difficulty', 'black_ai_difficulty'
            ])
    
    def save_game_stats(self, game):
        """Sauvegarde les statistiques d'une partie terminée."""
        # Extraire les informations de la partie
        game_id = game.id
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Déterminer le type de partie
        if game.white_ai and game.black_ai:
            game_type = "ai_vs_ai"
        elif game.white_ai:
            game_type = "ai_vs_human"
        elif game.black_ai:
            game_type = "human_vs_ai"
        else:
            game_type = "human_vs_human"
        
        # Déterminer les joueurs
        white_player = "AI" if game.white_ai else "Human"
        black_player = "AI" if game.black_ai else "Human"
        
        # Déterminer le gagnant et le résultat
        if game.winner == "white":
            winner = white_player
            result = "white_win"
        elif game.winner == "black":
            winner = black_player
            result = "black_win"
        else:
            winner = "Draw"
            result = "draw"
        
        # Compter les mouvements
        moves_count = game.board.history.length()
        
        # Calculer la durée (en secondes)
        if hasattr(game, 'start_time') and game.start_time:
            duration = (datetime.datetime.now() - game.start_time).total_seconds()
        else:
            duration = 0
        
        # Compter les pièces capturées
        white_captured = len(game.board.captured_pieces.get("white", []))
        black_captured = len(game.board.captured_pieces.get("black", []))
        
        # Difficulté de l'IA
        white_ai_difficulty = game.white_ai.difficulty if game.white_ai else "N/A"
        black_ai_difficulty = game.black_ai.difficulty if game.black_ai else "N/A"
        
        # Créer une nouvelle ligne de statistiques
        new_stats = pd.DataFrame({
            'game_id': [game_id],
            'date': [date],
            'game_type': [game_type],
            'white_player': [white_player],
            'black_player': [black_player],
            'winner': [winner],
            'moves_count': [moves_count],
            'duration': [duration],
            'result': [result],
            'white_captured': [white_captured],
            'black_captured': [black_captured],
            'white_ai_difficulty': [white_ai_difficulty],
            'black_ai_difficulty': [black_ai_difficulty]
        })
        
        # Ajouter les nouvelles statistiques au DataFrame
        self.stats_df = pd.concat([self.stats_df, new_stats], ignore_index=True)
        
        # Sauvegarder le DataFrame mis à jour
        self.stats_df.to_csv(self.stats_file, index=False)
        
        # Sauvegarder également l'historique des mouvements
        self._save_game_history(game)
        
        return True
    
    def _save_game_history(self, game):
        """Sauvegarde l'historique des mouvements d'une partie."""
        history_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'game_histories')
        os.makedirs(history_dir, exist_ok=True)
        
        # Sauvegarder l'historique en CSV
        history_file = os.path.join(history_dir, f'game_{game.id}_history.csv')
        game.board.history.save_to_csv(history_file)
    
    def get_stats_summary(self):
        """Retourne un résumé des statistiques de toutes les parties."""
        if self.stats_df.empty:
            return {
                'total_games': 0,
                'human_vs_human': 0,
                'human_vs_ai': 0,
                'ai_vs_ai': 0,
                'white_wins': 0,
                'black_wins': 0,
                'draws': 0,
                'avg_moves': 0,
                'avg_duration': 0
            }
        
        # Calculer les statistiques de base
        total_games = len(self.stats_df)
        human_vs_human = len(self.stats_df[self.stats_df['game_type'] == 'human_vs_human'])
        human_vs_ai = len(self.stats_df[(self.stats_df['game_type'] == 'human_vs_ai') | 
                                        (self.stats_df['game_type'] == 'ai_vs_human')])
        ai_vs_ai = len(self.stats_df[self.stats_df['game_type'] == 'ai_vs_ai'])
        
        white_wins = len(self.stats_df[self.stats_df['result'] == 'white_win'])
        black_wins = len(self.stats_df[self.stats_df['result'] == 'black_win'])
        draws = len(self.stats_df[self.stats_df['result'] == 'draw'])
        
        avg_moves = self.stats_df['moves_count'].mean() if 'moves_count' in self.stats_df else 0
        avg_duration = self.stats_df['duration'].mean() if 'duration' in self.stats_df else 0
        
        return {
            'total_games': total_games,
            'human_vs_human': human_vs_human,
            'human_vs_ai': human_vs_ai,
            'ai_vs_ai': ai_vs_ai,
            'white_wins': white_wins,
            'black_wins': black_wins,
            'draws': draws,
            'avg_moves': avg_moves,
            'avg_duration': avg_duration
        }
    
    def generate_charts(self):
        """Génère des graphiques pour visualiser les statistiques."""
        if self.stats_df.empty:
            return None
            
        # Vérifier si nous sommes dans le thread principal
        if not is_main_thread:
            return None
        
        try:
            # Créer un timestamp unique pour les fichiers
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Graphique des résultats (victoires blancs/noirs/nuls)
            results_counts = self.stats_df['result'].value_counts()
            plt.figure(figsize=(10, 6))
            results_counts.plot(kind='bar', color=['#3498db', '#2ecc71', '#e74c3c'])
            plt.title('Résultats des parties')
            plt.xlabel('Résultat')
            plt.ylabel('Nombre de parties')
            plt.tight_layout()
            results_chart_path = os.path.join(self.charts_dir, f'results_{timestamp}.png')
            plt.savefig(results_chart_path)
            plt.close()
            
            # 2. Graphique des types de parties
            game_types = self.stats_df['game_type'].value_counts()
            plt.figure(figsize=(10, 6))
            game_types.plot(kind='pie', autopct='%1.1f%%')
            plt.title('Types de parties')
            plt.axis('equal')
            plt.tight_layout()
            types_chart_path = os.path.join(self.charts_dir, f'game_types_{timestamp}.png')
            plt.savefig(types_chart_path)
            plt.close()
            
            # 3. Graphique du nombre de mouvements par partie
            plt.figure(figsize=(12, 6))
            plt.hist(self.stats_df['moves_count'], bins=20, color='#9b59b6')
            plt.title('Distribution du nombre de mouvements par partie')
            plt.xlabel('Nombre de mouvements')
            plt.ylabel('Nombre de parties')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            moves_chart_path = os.path.join(self.charts_dir, f'moves_count_{timestamp}.png')
            plt.savefig(moves_chart_path)
            plt.close()
            
            # 4. Graphique de la durée des parties
            plt.figure(figsize=(12, 6))
            plt.hist(self.stats_df['duration'], bins=20, color='#f39c12')
            plt.title('Distribution de la durée des parties')
            plt.xlabel('Durée (secondes)')
            plt.ylabel('Nombre de parties')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            duration_chart_path = os.path.join(self.charts_dir, f'duration_{timestamp}.png')
            plt.savefig(duration_chart_path)
            plt.close()
            
            return {
                'results_chart': os.path.basename(results_chart_path),
                'types_chart': os.path.basename(types_chart_path),
                'moves_chart': os.path.basename(moves_chart_path),
                'duration_chart': os.path.basename(duration_chart_path)
            }
            
        except Exception as e:
            print(f"Erreur lors de la génération des graphiques: {e}")
            return None
    
    def get_recent_games(self, limit=10):
        """Retourne les parties les plus récentes."""
        if self.stats_df.empty:
            return []
        
        # Trier par date (la plus récente en premier) et prendre les 'limit' premières
        recent_games = self.stats_df.sort_values('date', ascending=False).head(limit)
        
        # Convertir en liste de dictionnaires pour faciliter l'utilisation dans les templates
        return recent_games.to_dict('records')
    
    def get_game_stats(self, game_id):
        """Retourne les statistiques détaillées d'une partie spécifique."""
        if self.stats_df.empty:
            return None
        
        # Filtrer pour obtenir la partie spécifique
        game_stats = self.stats_df[self.stats_df['game_id'] == game_id]
        
        if game_stats.empty:
            return None
        
        # Convertir en dictionnaire
        return game_stats.iloc[0].to_dict()
    
    def get_ai_performance(self):
        """Analyse la performance de l'IA selon les niveaux de difficulté."""
        if self.stats_df.empty:
            return {}
        
        # Filtrer les parties avec IA
        ai_games = self.stats_df[(self.stats_df['white_player'] == 'AI') | 
                                 (self.stats_df['black_player'] == 'AI')]
        
        if ai_games.empty:
            return {}
        
        # Analyser les performances par niveau de difficulté
        difficulty_levels = ['easy', 'medium', 'hard']
        performance = {}
        
        for difficulty in difficulty_levels:
            # IA jouant en blanc
            white_ai = ai_games[ai_games['white_ai_difficulty'] == difficulty]
            white_wins = len(white_ai[white_ai['result'] == 'white_win'])
            white_losses = len(white_ai[white_ai['result'] == 'black_win'])
            white_draws = len(white_ai[white_ai['result'] == 'draw'])
            white_total = len(white_ai)
            
            # IA jouant en noir
            black_ai = ai_games[ai_games['black_ai_difficulty'] == difficulty]
            black_wins = len(black_ai[black_ai['result'] == 'black_win'])
            black_losses = len(black_ai[black_ai['result'] == 'white_win'])
            black_draws = len(black_ai[black_ai['result'] == 'draw'])
            black_total = len(black_ai)
            
            # Total pour ce niveau de difficulté
            total_games = white_total + black_total
            total_wins = white_wins + black_wins
            total_losses = white_losses + black_losses
            total_draws = white_draws + black_draws
            
            # Calculer le taux de victoire
            win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
            
            performance[difficulty] = {
                'total_games': total_games,
                'wins': total_wins,
                'losses': total_losses,
                'draws': total_draws,
                'win_rate': win_rate
            }
        
        return performance