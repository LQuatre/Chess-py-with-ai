class Move:
    def __init__(self, start_pos, end_pos):
        self.start_pos = start_pos  # (ligne, colonne)
        self.end_pos = end_pos      # (ligne, colonne)

    def is_valid(self, board):
        """ Vérifie si un mouvement est valide (simplifié pour l'instant). """
        # Empêche de sortir du plateau
        if not all(0 <= x < 8 for x in self.start_pos + self.end_pos):
            return False

        # Règles spécifiques aux pièces (à compléter)
        return True

    def to_chess_notation(self):
        """ Convertit les positions en notation échiquéenne. """
        def pos_to_notation(pos):
            columns = 'abcdefgh'
            return columns[pos[1]] + str(pos[0] + 1)

        return pos_to_notation(self.start_pos) + pos_to_notation(self.end_pos)
