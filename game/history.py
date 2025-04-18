import pandas as pd
import threading
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend which doesn't require a GUI
# Vérifier si nous sommes dans le thread principal
is_main_thread = threading.current_thread() is threading.main_thread()
import matplotlib.pyplot as plt
import tabulate

class GameHistory:
    def __init__(self):
        """ Initialise un historique des coups avec notation échiquéenne. """
        self.moves = pd.DataFrame(columns=['Tour', 'Joueur', 'Mouvement', 'Pice', 'Position', 'start', 'end'])

    @staticmethod
    def to_chess_notation(start, end):
        """ Convertit une position (x, y) en notation échiquéenne. """
        columns = "abcdefgh"
        return f"{columns[start[1]]}{8 - start[0]}{columns[end[1]]}{8 - end[0]}"

    def add_move(self, tour, joueur, start, end, piece, position):
        """ Ajoute un coup dans l'historique au format SAN. """
        move_notation = self.to_chess_notation(start, end)
        new_move = pd.DataFrame({'Tour': [tour], 'Joueur': [joueur], 'Mouvement': [move_notation], 'Piece': [piece], 'Position': [position], 'start': [start], 'end': [end]})
        self.moves = pd.concat([self.moves, new_move], ignore_index=True)

    def save_to_csv(self, filename="game_history.csv"):
        """ Sauvegarde l'historique en CSV. """
        self.moves.to_csv(filename, index=False)

    def display_history(self):
        """ Affiche l'historique des coups sous forme de tableau et graphique. """
        if self.moves.empty:
            print("Aucun coup n'a été joué.")
            return

        # Affichage sous forme de tableau
        print("Historique des coups :")
        print(tabulate.tabulate(self.moves, headers='keys', tablefmt='grid', showindex=False))

    def length(self):
        """ Retourne le nombre de coups dans l'historique. """
        return len(self.moves)
    
    def get_last_move(self):
        """ Retourne le dernier coup joué. """
        if self.moves.empty:
            return None
        return self.moves.iloc[-1]
    
    def get_history(self):
        """ Retourne l'historique complet des coups. """
        return self.moves.copy()