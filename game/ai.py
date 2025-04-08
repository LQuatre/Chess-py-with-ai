import random
from game.move import Move

class AI:
    def __init__(self, color="black"):
        self.color = color

    def get_best_move(self, board):
        """ Sélectionne un mouvement aléatoire (à améliorer avec Minimax). """
        possible_moves = [((6, i), (5, i)) for i in range(8)]  # Ex: déplacement des pions
        return random.choice(possible_moves)

# Test rapide
if __name__ == "__main__":
    ai = AI()
    print(ai.get_best_move(None))
