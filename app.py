from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash, flash
from routes.board_routes import board_routes
from game.game_stats import GameStats
from game.game_manager import GameManager
import uuid
import os
import numpy as np
import threading
import time

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète'  # Nécessaire pour les sessions

# Enregistrer le blueprint avant de définir les routes
app.register_blueprint(board_routes)

# Fonction pour s'assurer que l'utilisateur a un ID
def ensure_player_id():
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    return session['player_id']

# Route pour la page d'accueil
@app.route('/')
def home():
    ensure_player_id()
    return render_template('index.html')

# Route pour afficher les statistiques des parties
@app.route('/stats')
def game_stats():
    # Obtenir les statistiques
    stats_manager = GameStats.get_instance()
    summary = stats_manager.get_stats_summary()
    recent_games = stats_manager.get_recent_games(10)
    ai_performance = stats_manager.get_ai_performance()
    
    # Générer des graphiques
    charts = stats_manager.generate_charts()
    
    return render_template(
        'stats.html',
        summary=summary,
        recent_games=recent_games,
        ai_performance=ai_performance,
        charts=charts
    )

# Route pour créer une nouvelle partie
@app.route('/new-game', methods=['GET'])
def new_game():
    player_id = ensure_player_id()
    game_type = request.args.get('type', 'human_vs_human')
    ai_difficulty = request.args.get('difficulty', 'medium')
    
    game_manager = GameManager.get_instance()
    
    if game_type == 'human_vs_human':
        game_id = game_manager.create_game()
    elif game_type == 'human_vs_ai':
        human_color = request.args.get('color', 'white')
        game_id = game_manager.create_human_vs_ai_game(human_color, ai_difficulty)
    elif game_type == 'ai_vs_ai':
        white_difficulty = request.args.get('white_difficulty', ai_difficulty)
        black_difficulty = request.args.get('black_difficulty', ai_difficulty)
        game_id = game_manager.create_ai_vs_ai_game(white_difficulty, black_difficulty)
    else:
        game_id = game_manager.create_game()
    
    # Si c'est une partie avec un joueur humain, le faire rejoindre la partie
    if game_type != 'ai_vs_ai':
        game_manager.join_game(game_id, player_id)
    
    return redirect(url_for('display_board', game_id=game_id))

# Route pour rejoindre une partie existante
@app.route('/join-game/<game_id>', methods=['GET'])
def join_game(game_id):
    player_id = ensure_player_id()
    game_manager = GameManager.get_instance()
    success, message = game_manager.join_game(game_id, player_id)
    if success:
        return redirect(url_for('display_board', game_id=game_id))
    else:
        return render_template('index.html', error=message)

# Route pour lister les parties disponibles
@app.route('/available-games', methods=['GET'])
def list_available_games():
    game_manager = GameManager.get_instance()
    available_games = game_manager.list_available_games()
    return render_template('available_games.html', games=available_games)

# Route pour afficher le plateau d'échecs
@app.route('/chess-board', methods=['GET'])
def display_board():
    player_id = ensure_player_id()
    game_id = request.args.get('game_id')
    
    if not game_id:
        # Si aucun game_id n'est fourni, vérifier si le joueur est déjà dans une partie
        game_manager = GameManager.get_instance()
        game_id = game_manager.get_player_game(player_id)
        
        if not game_id:
            # Si le joueur n'est pas dans une partie, rediriger vers la liste des parties
            return redirect(url_for('list_available_games'))
    
    game_manager = GameManager.get_instance()
    game = game_manager.get_game(game_id)
    
    if not game:
        return redirect(url_for('list_available_games'))
    
    # Rejoindre la partie si ce n'est pas déjà fait
    game_manager.join_game(game_id, player_id)
    
    player_color = game_manager.get_player_color(game_id, player_id)
    board_state = game.board.to_list()
    
    return render_template('board.html', 
                          board=board_state, 
                          turn=game.turn, 
                          game_over=game.game_over, 
                          winner=game.winner,
                          game_id=game_id,
                          player_color=player_color)

# Route pour réinitialiser le jeu
@app.route('/reset-game/<game_id>', methods=['GET'])
def reset_game(game_id):
    player_id = ensure_player_id()
    game_manager = GameManager.get_instance()
    game = game_manager.get_game(game_id)
    
    if game:
        # Vérifier si le joueur est dans cette partie
        if game_manager.get_player_color(game_id, player_id):
            # Créer une nouvelle partie avec le même ID
            game_manager.games[game_id] = Game()
    
    return redirect(url_for('display_board', game_id=game_id))

# Route pour récupérer une partie
@app.route('/recover-game/<game_id>', methods=['GET'])
def recover_game(game_id):
    player_id = ensure_player_id()
    game_manager = GameManager.get_instance()
    
    # Vérifier si la partie existe
    game = game_manager.get_game(game_id)
    if not game:
        flash("La partie demandée n'existe pas ou a expiré.", "danger")
        return redirect(url_for('list_available_games'))
    
    # Essayer de rejoindre la partie
    success, message = game_manager.join_game(game_id, player_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "warning")
    
    return redirect(url_for('display_board', game_id=game_id))

# Route pour obtenir l'état actuel du jeu (pour les mises à jour AJAX)
@app.route('/game-state', methods=['GET'])
def get_game_state():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({'error': 'Game ID is required'}), 400
        
    game_manager = GameManager.get_instance()
    game = game_manager.get_game(game_id)
    
    if not game:
        # Check if this is a persistent issue
        if 'game_not_found_count' not in session:
            session['game_not_found_count'] = 1
        else:
            session['game_not_found_count'] += 1
            
        # If we've tried multiple times, suggest creating a new game
        if session.get('game_not_found_count', 0) > 3:
            return jsonify({
                'error': 'Game not found',
                'message': 'La partie a peut-être expiré ou été supprimée.',
                'action': 'new_game'
            }), 404
        
        return jsonify({'error': 'Game not found'}), 404
        
    # Reset the counter if we successfully found the game
    if 'game_not_found_count' in session:
        session.pop('game_not_found_count')
        
    return jsonify(game.get_game_state())

# Route pour effectuer un mouvement
@app.route('/move', methods=['POST'])
def make_move():
    try:
        data = request.json
        
        # Vérifier si les clés nécessaires sont présentes
        if 'from' in data and 'to' in data and 'game_id' in data:
            game_id = data['game_id']
            from_pos = data['from']
            to_pos = data['to']
            
            game_manager = GameManager.get_instance()
            game = game_manager.get_game(game_id)
            
            if not game:
                return jsonify({'success': False, 'error': 'Game not found'}), 404
                
            # Exécuter le mouvement
            success, message = game.play_turn(from_pos, to_pos)
            
            # Vérifier s'il y a une promotion en attente
            promotion_pending = game.board.has_promotion_pending()
            success, message = game.play_turn(from_pos, to_pos)
            # Préparer la réponse
            response = {
                'success': success,
                'message': message,
                'game_state': game.get_game_state(),
                'promotion_pending': promotion_pending
            }
            return jsonify(response)
        
            return jsonify(response)
        
        return jsonify({'success': False, 'error': 'Invalid request data'})
    
    except Exception as e:
        app.logger.error(f"Erreur lors du traitement du mouvement: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500

# Route pour obtenir les mouvements valides d'une pièce
@app.route('/valid-moves', methods=['GET'])
def get_valid_moves():
    position = request.args.get('position')
    game_id = request.args.get('game_id')
    
    if not position or not game_id:
        return jsonify({'success': False, 'error': 'Position and game_id are required'}), 400
        
    game_manager = GameManager.get_instance()
    game = game_manager.get_game(game_id)
    
    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404
        
    # Convertir la position en indices de tableau
    row, col = game.board.chess_notation_to_index(position)
    
    # Obtenir les mouvements valides
    valid_moves = game.board.get_valid_moves(row, col)
    
    # Convertir les indices en notation d'échecs
    valid_moves_notation = []
    for move_row, move_col in valid_moves:
        file = chr(move_col + ord('a'))
        rank = 8 - move_row
        valid_moves_notation.append(f"{file}{rank}")
    
    return jsonify({
        'success': True,
        'valid_moves': valid_moves_notation
    })

# Route pour promouvoir un pion
@app.route('/promote', methods=['POST'])
def promote_pawn():
    data = request.json
    
    # Vérifier si les clés nécessaires sont présentes
    if 'piece_type' in data and 'game_id' in data:
        game_id = data['game_id']
        game_manager = GameManager.get_instance()
        game = game_manager.get_game(game_id)
        
        if not game:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
            
        promotion_info = game.board.get_promotion_info()
        
        if not promotion_info:
            return jsonify({'success': False, 'error': 'No pawn to promote'})
            
        # Promouvoir le pion
        success = game.board.promote_pawn(
            promotion_info['row'], 
            promotion_info['col'], 
            data['piece_type']
        )
        
        return jsonify({
            'success': success,
            'game_state': game.get_game_state()
        })
    return jsonify({'success': False, 'error': 'Invalid request data'})

# Route pour changer le type de joueur (humain ou IA)
@app.route('/set-player-type', methods=['POST'])
def set_player_type():
    data = request.json
    
    # Vérifier si les clés nécessaires sont présentes
    if 'color' in data and 'player_type' in data and 'game_id' in data:
        game_id = data['game_id']
        color = data['color']
        player_type = data['player_type']
        ai_difficulty = data.get('ai_difficulty', 'medium')
        
        game_manager = GameManager.get_instance()
        success, message = game_manager.set_player_type(game_id, color, player_type, ai_difficulty)
        
        return jsonify({
            'success': success,
            'message': message,
            'game_state': game_manager.get_game(game_id).get_game_state() if success else None
        })
    return jsonify({'success': False, 'error': 'Invalid request data'})

# Route alternative pour la compatibilité avec les anciennes URL
@app.route('/game-state/<game_id>', methods=['GET'])
def get_game_state_by_id(game_id):
    # Rediriger vers la nouvelle route
    # Rediriger vers la nouvelle route
    return get_game_state()

# Route pour récupérer les chemins de pensée de l'IA
@app.route('/ai-thoughts', methods=['GET'])
def get_ai_thoughts():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({'error': 'Game ID is required'}), 400
        
    game_manager = GameManager.get_instance()
    game = game_manager.get_game(game_id)
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    # Récupérer les pensées de l'IA blanche et noire si elles existent
    white_thoughts = []
    black_thoughts = []
    
    # Limiter le nombre de pensées récupérées pour améliorer les performances
    if game.white_ai:
        white_thoughts = game.white_ai.get_thought_log()  # Déjà limité à 10 entrées dans la méthode
    
    if game.black_ai:
        black_thoughts = game.black_ai.get_thought_log()  # Déjà limité à 10 entrées dans la méthode
    
    # Utiliser une réponse compacte pour réduire la taille des données
    return jsonify({
        'white_player_type': game.white_player_type,
        'black_player_type': game.black_player_type,
        'white_thoughts': white_thoughts,
        'black_thoughts': black_thoughts
    })



# Route pour consulter les parties sauvegardées
@app.route('/saved-games', methods=['GET'])
def list_saved_games():
    from datetime import datetime
    import csv
    
    # Utiliser un chemin absolu pour le dossier saved_games
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, 'saved_games')
    
    if not os.path.exists(save_dir):
        return render_template('saved_games.html', games=[])
    
    all_files = os.listdir(save_dir)
    games = []
    
    # Parcourir tous les fichiers du répertoire
    for filename in all_files:
        if filename.endswith('.csv'):
            file_path = os.path.join(save_dir, filename)
            try:
                # Extraire l'ID du nom du fichier, en tenant compte du suffixe _history
                game_id = filename.replace('game_', '').replace('_history.csv', '').replace('.csv', '')
                
                # Lire le fichier CSV pour extraire les informations
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    
            # Lire l'en-tête pour obtenir les noms des colonnes
                    header = next(csv_reader, None)
                    print(f"En-tête CSV: {header}")
                    
                    # Initialiser les données par défaut
                    white_player = 'human'
                    black_player = 'human'
                    winner = 'En cours'
                    timestamp = ''
                    moves_count = 0
                    
                    # Déterminer les indices des colonnes en fonction de l'en-tête
                    tour_idx = header.index('Tour') if 'Tour' in header else -1
                    joueur_idx = header.index('Joueur') if 'Joueur' in header else -1
                    mouvement_idx = header.index('Mouvement') if 'Mouvement' in header else -1
                    position_idx = header.index('Position') if 'Position' in header else -1
                    
                    print(f"Indices des colonnes: Tour={tour_idx}, Joueur={joueur_idx}, Mouvement={mouvement_idx}, Position={position_idx}")
                    
                    # Lire toutes les lignes pour analyser les mouvements
                    rows = list(csv_reader)
                    moves_count = len(rows)
                    print(f"Nombre de mouvements: {moves_count}")
                    
                    # Déterminer les types de joueurs en fonction des données
                    white_moves = [row for row in rows if joueur_idx >= 0 and joueur_idx < len(row) and row[joueur_idx] == 'White']
                    black_moves = [row for row in rows if joueur_idx >= 0 and joueur_idx < len(row) and row[joueur_idx] == 'Black']
                    
                    # Déterminer le gagnant en cherchant "ÉCHEC" et "mat" dans la dernière ligne
                    if rows and position_idx >= 0 and position_idx < len(rows[-1]):
                        last_position = rows[-1][position_idx]
                        if 'ÉCHEC' in last_position and 'mat' in last_position.lower():
                            # Le gagnant est l'opposé du dernier joueur qui a joué
                            last_player = rows[-1][joueur_idx] if joueur_idx >= 0 and joueur_idx < len(rows[-1]) else ''
                            winner = 'white' if last_player == 'Black' else 'black'
                    
                    # Utiliser la date de modification du fichier pour le timestamp
                    mod_time = os.path.getmtime(file_path)
                    timestamp = datetime.fromtimestamp(mod_time).isoformat()
                
                # Créer l'objet d'information de jeu
                game_info = {
                    'id': game_id,
                    'white_player': white_player,
                    'black_player': black_player,
                    'winner': winner,
                    'timestamp': timestamp,
                    'moves': moves_count,
                    'file_path': file_path
                }
                
                # Convertir le timestamp en format lisible
                if game_info['timestamp']:
                    try:
                        dt = datetime.fromisoformat(game_info['timestamp'])
                        game_info['date'] = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        game_info['date'] = game_info['timestamp']
                else:
                    # Utiliser la date de modification du fichier si pas de timestamp
                    mod_time = os.path.getmtime(file_path)
                    dt = datetime.fromtimestamp(mod_time)
                    game_info['date'] = dt.strftime('%d/%m/%Y %H:%M')
                    game_info['timestamp'] = dt.isoformat()
                
                games.append(game_info)
                print(f"Partie ajoutée: {game_info}")
                
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier CSV {filename}: {e}")
    
    # Trier les parties par date (les plus récentes d'abord)
    games.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    print(f"Nombre total de parties trouvées: {len(games)}")
    return render_template('saved_games.html', games=games)

# Route pour visualiser une partie sauvegardée
@app.route('/view-saved-game/<game_id>', methods=['GET'])
def view_saved_game(game_id):
    import os
    import csv
    
    # Vérifier si le fichier CSV existe (avec ou sans le suffixe _history)
    csv_path = os.path.join(os.path.dirname(__file__), 'saved_games', f'game_{game_id}.csv')
    csv_history_path = os.path.join(os.path.dirname(__file__), 'saved_games', f'game_{game_id}_history.csv')
    
    print(f"Tentative d'ouverture du fichier pour le jeu {game_id}")
    print(f"Chemin standard: {csv_path}, existe: {os.path.exists(csv_path)}")
    print(f"Chemin historique: {csv_history_path}, existe: {os.path.exists(csv_history_path)}")
    
    # Déterminer quel fichier utiliser
    if os.path.exists(csv_path):
        file_path = csv_path
        print(f"Utilisation du fichier: {file_path}")
    elif os.path.exists(csv_history_path):
        file_path = csv_history_path
        print(f"Utilisation du fichier: {file_path}")
    else:
        print(f"Aucun fichier trouvé pour le jeu {game_id}")
        return redirect(url_for('list_saved_games'))
    
    try:
        # Initialiser les données par défaut
        # Créer un plateau vide (8x8)
        board_state = [["" for _ in range(8)] for _ in range(8)]
        
        # Initialiser le plateau avec les pièces de départ
        # Pièces noires (rangée 0 et 1)
        board_state[0][0] = "♜"  # Tour noire
        board_state[0][1] = "♞"  # Cavalier noir
        board_state[0][2] = "♝"  # Fou noir
        board_state[0][3] = "♛"  # Dame noire
        board_state[0][4] = "♚"  # Roi noir
        board_state[0][5] = "♝"  # Fou noir
        board_state[0][6] = "♞"  # Cavalier noir
        board_state[0][7] = "♜"  # Tour noire
        for i in range(8):
            board_state[1][i] = "♟"  # Pions noirs
        
        # Pièces blanches (rangée 6 et 7)
        board_state[7][0] = "♖"  # Tour blanche
        board_state[7][1] = "♘"  # Cavalier blanc
        board_state[7][2] = "♗"  # Fou blanc
        board_state[7][3] = "♕"  # Dame blanche
        board_state[7][4] = "♔"  # Roi blanc
        board_state[7][5] = "♗"  # Fou blanc
        board_state[7][6] = "♘"  # Cavalier blanc
        board_state[7][7] = "♖"  # Tour blanche
        for i in range(8):
            board_state[6][i] = "♙"  # Pions blancs
        
        turn = 'white'
        game_over = False
        winner = None
        white_player_type = 'human'
        black_player_type = 'human'
        history = []
        
        # Fonction pour convertir la notation d'échecs en indices de tableau
        def chess_notation_to_index(notation):
            if not notation or len(notation) < 2:
                return -1, -1
            try:
                col = ord(notation[0].lower()) - ord('a')
                row = 8 - int(notation[1])
                return row, col
            except:
                return -1, -1
        
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            
            # Lire l'en-tête
            header = next(csv_reader, None)
            print(f"En-tête CSV: {header}")
            
            # Déterminer les indices des colonnes en fonction de l'en-tête
            tour_idx = header.index('Tour') if 'Tour' in header else -1
            joueur_idx = header.index('Joueur') if 'Joueur' in header else -1
            mouvement_idx = header.index('Mouvement') if 'Mouvement' in header else -1
            piece_idx = -1
            if 'Piece' in header:
                piece_idx = header.index('Piece')
            elif 'Pice' in header:  # Correction pour une possible faute d'orthographe
                piece_idx = header.index('Pice')
            position_idx = header.index('Position') if 'Position' in header else -1
            start_idx = header.index('start') if 'start' in header else -1
            end_idx = header.index('end') if 'end' in header else -1
            
            print(f"Indices des colonnes: Tour={tour_idx}, Joueur={joueur_idx}, Mouvement={mouvement_idx}, Piece={piece_idx}, Position={position_idx}, start={start_idx}, end={end_idx}")
            
            # Définir les types de joueurs par défaut
            white_player_type = 'human'
            black_player_type = 'human'
            
            # Lire l'historique des mouvements
            for row in csv_reader:
                if len(row) > mouvement_idx and mouvement_idx >= 0:
                    # Extraire les informations du mouvement
                    mouvement = row[mouvement_idx]
                    joueur = row[joueur_idx] if joueur_idx >= 0 and joueur_idx < len(row) else 'Unknown'
                    piece_symbol = row[piece_idx] if piece_idx >= 0 and piece_idx < len(row) else ''
                    position = row[position_idx] if position_idx >= 0 and position_idx < len(row) else ''
                    
                    # Extraire les positions de départ et d'arrivée du mouvement (format e2e4)
                    from_pos = ''
                    to_pos = ''
                    
                    if len(mouvement) >= 4:
                        from_pos = mouvement[:2]
                        to_pos = mouvement[2:4]
                    else:
                        # Utiliser les coordonnées start et end si disponibles
                        if start_idx >= 0 and start_idx < len(row):
                            start_str = row[start_idx]
                            # Convertir le format de tuple en notation d'échecs
                            if start_str.startswith('(') and start_str.endswith(')'):
                                try:
                                    # Format "(row, col)" -> convertir en notation d'échecs
                                    coords = start_str.strip('()').split(',')
                                    if len(coords) == 2:
                                        row_idx = int(coords[0].strip())
                                        col_idx = int(coords[1].strip())
                                        # Convertir en notation d'échecs (a1, b2, etc.)
                                        from_pos = chr(ord('a') + col_idx) + str(8 - row_idx)
                                except Exception as e:
                                    print(f"Erreur lors de la conversion de la position de départ {start_str}: {e}")
                            else:
                                from_pos = start_str
                        
                        if end_idx >= 0 and end_idx < len(row):
                            end_str = row[end_idx]
                            # Convertir le format de tuple en notation d'échecs
                            if end_str.startswith('(') and end_str.endswith(')'):
                                try:
                                    # Format "(row, col)" -> convertir en notation d'échecs
                                    coords = end_str.strip('()').split(',')
                                    if len(coords) == 2:
                                        row_idx = int(coords[0].strip())
                                        col_idx = int(coords[1].strip())
                                        # Convertir en notation d'échecs (a1, b2, etc.)
                                        to_pos = chr(ord('a') + col_idx) + str(8 - row_idx)
                                except Exception as e:
                                    print(f"Erreur lors de la conversion de la position d'arrivée {end_str}: {e}")
                            else:
                                to_pos = end_str
                    
                    # Vérifier si le mouvement contient une indication d'échec
                    check = 'ÉCHEC' in position if position else False
                    
                    # Créer l'objet de mouvement
                    move = {
                        'tour': row[tour_idx] if tour_idx >= 0 and tour_idx < len(row) else '',
                        'joueur': joueur,
                        'from': from_pos,
                        'to': to_pos,
                        'piece': piece_symbol,
                        'position': position,
                        'check': check
                    }
                    
                    history.append(move)
                    
                    # Appliquer le mouvement au plateau
                    from_row, from_col = chess_notation_to_index(from_pos)
                    to_row, to_col = chess_notation_to_index(to_pos)
                    
                    if from_row >= 0 and from_col >= 0 and to_row >= 0 and to_col >= 0:
                        # Obtenir la pièce à déplacer
                        piece = board_state[from_row][from_col]
                        
                        # Si la pièce n'est pas trouvée mais que nous avons l'information de la pièce
                        if not piece and piece_symbol:
                            piece = piece_symbol
                        
                        # Déplacer la pièce
                        if piece:
                            board_state[to_row][to_col] = piece
                            board_state[from_row][from_col] = ""
                    
                    # Déterminer le gagnant si le dernier coup est un échec et mat
                    if 'ÉCHEC' in position and 'mat' in position.lower():
                        winner = 'white' if joueur == 'Black' else 'black'
                        game_over = True
            
            # Déterminer l'état final du jeu
            if winner:
                game_over = True
            
            # Déterminer le tour actuel
            if len(history) % 2 == 0:
                turn = 'white'
            else:
                turn = 'black'
            
            print(f"Nombre total de mouvements: {len(history)}")
        
        return render_template('view_saved_game.html', 
                              board=board_state,
                              turn=turn,
                              game_over=game_over,
                              winner=winner,
                              white_player_type=white_player_type,
                              black_player_type=black_player_type,
                              history=history,
                              game_id=game_id)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        return redirect(url_for('list_saved_games'))

# Route pour les statistiques de l'IA
@app.route('/ai-stats', methods=['GET'])
def ai_stats():
    import os
    import json
    import numpy as np
    import pandas as pd
    import glob
    from game.game_manager import GameManager
    
    # Récupérer les statistiques des parties sauvegardées
    save_dir = os.path.join(os.path.dirname(__file__), 'saved_games')
    
    if not os.path.exists(save_dir):
        return render_template('ai_stats.html', stats={}, ai_performance={}, performance_data=[])
    
    stats = {
        'total_games': 0,
        'ai_wins': 0,
        'human_wins': 0,
        'draws': 0,
        'ai_vs_ai': 0,
        'human_vs_ai': 0,
        'human_vs_human': 0,
        'avg_moves': 0,
        'total_moves': 0,
        'white_wins': 0,
        'black_wins': 0,
        'difficulty_stats': {
            'easy': {'games': 0, 'wins': 0, 'losses': 0, 'draws': 0},
            'medium': {'games': 0, 'wins': 0, 'losses': 0, 'draws': 0},
            'hard': {'games': 0, 'wins': 0, 'losses': 0, 'draws': 0}
        },
        'avg_time_per_move': 0,
        'total_time': 0,
        'move_times': []
    }
    
    # Statistiques de performance de l'IA
    ai_performance = {
        'avg_nodes_evaluated': 0,
        'total_nodes_evaluated': 0,
        'avg_evaluation_time': 0,
        'max_evaluation_time': 0,
        'min_evaluation_time': float('inf'),
        'evaluation_times': [],
        'move_times': []
    }
    
    # Récupérer les données de performance des fichiers CSV
    performance_data = []
    charts_dir = os.path.join(os.path.dirname(__file__), 'game', 'charts')
    
    if os.path.exists(charts_dir):
        # Trouver tous les fichiers CSV dans le dossier charts
        csv_files = glob.glob(os.path.join(charts_dir, 'performance_data_*.csv'))
        
        # Trier les fichiers par date (du plus récent au plus ancien)
        csv_files.sort(reverse=True)
        
        # Limiter à 10 fichiers pour éviter de surcharger la page
        csv_files = csv_files[:10]
        
        for csv_file in csv_files:
            try:
                # Extraire le timestamp du nom du fichier
                filename = os.path.basename(csv_file)
                timestamp = filename.replace('performance_data_', '').replace('.csv', '')
                
                # Lire le fichier CSV
                df = pd.read_csv(csv_file)
                
                # Convertir en liste de dictionnaires pour le template
                data = {
                    'timestamp': timestamp,
                    'filename': filename,
                    'data': df.to_dict('records'),
                    'avg_move_time': df['Move Time (s)'].mean() if 'Move Time (s)' in df.columns else 0,
                    'avg_eval_time': df['Evaluation Time (ms)'].mean() if 'Evaluation Time (ms)' in df.columns else 0,
                    'max_move_time': df['Move Time (s)'].max() if 'Move Time (s)' in df.columns else 0,
                    'max_eval_time': df['Evaluation Time (ms)'].max() if 'Evaluation Time (ms)' in df.columns else 0,
                    'move_count': len(df)
                }
                
                performance_data.append(data)
                
                # Ajouter ces données aux statistiques globales
                if 'Move Time (s)' in df.columns:
                    ai_performance['move_times'].extend(df['Move Time (s)'].tolist())
                
                if 'Evaluation Time (ms)' in df.columns:
                    eval_times_seconds = [t/1000 for t in df['Evaluation Time (ms)'].tolist()]
                    ai_performance['evaluation_times'].extend(eval_times_seconds)
                
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier CSV {csv_file}: {e}")
    
    
    # Récupérer les parties actives pour les statistiques en temps réel
    game_manager = GameManager.get_instance()
    active_games = game_manager.games
    
    # Collecter les statistiques des parties actives
    for game_id, game in active_games.items():
        if hasattr(game, 'white_ai') and game.white_ai:
            if hasattr(game.white_ai, 'move_times') and game.white_ai.move_times:
                stats['move_times'].extend(game.white_ai.move_times)
                ai_performance['move_times'].extend(game.white_ai.move_times)
            
            if hasattr(game.white_ai, 'evaluation_times') and game.white_ai.evaluation_times:
                ai_performance['evaluation_times'].extend(game.white_ai.evaluation_times)
            
            if hasattr(game.white_ai, 'nodes_evaluated'):
                ai_performance['total_nodes_evaluated'] += game.white_ai.nodes_evaluated
        
        if hasattr(game, 'black_ai') and game.black_ai:
            if hasattr(game.black_ai, 'move_times') and game.black_ai.move_times:
                stats['move_times'].extend(game.black_ai.move_times)
                ai_performance['move_times'].extend(game.black_ai.move_times)
            
            if hasattr(game.black_ai, 'evaluation_times') and game.black_ai.evaluation_times:
                ai_performance['evaluation_times'].extend(game.black_ai.evaluation_times)
            
            if hasattr(game.black_ai, 'nodes_evaluated'):
                ai_performance['total_nodes_evaluated'] += game.black_ai.nodes_evaluated
    
    # Collecter les statistiques des parties sauvegardées
    for filename in os.listdir(save_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(save_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    game_data = json.load(f)
                
                stats['total_games'] += 1
                
                # Compter les types de parties
                white_type = game_data.get('white_player_type', 'human')
                black_type = game_data.get('black_player_type', 'human')
                
                if white_type == 'ai' and black_type == 'ai':
                    stats['ai_vs_ai'] += 1
                elif white_type == 'human' and black_type == 'human':
                    stats['human_vs_human'] += 1
                else:
                    stats['human_vs_ai'] += 1
                
                # Compter les victoires
                winner = game_data.get('winner')
                if winner == 'white':
                    stats['white_wins'] += 1
                    if white_type == 'ai':
                        stats['ai_wins'] += 1
                        # Ajouter aux statistiques par difficulté
                        difficulty = game_data.get('white_ai_difficulty', 'medium')
                        if difficulty in stats['difficulty_stats']:
                            stats['difficulty_stats'][difficulty]['wins'] += 1
                            stats['difficulty_stats'][difficulty]['games'] += 1
                    else:
                        stats['human_wins'] += 1
                        # Si l'adversaire était une IA, compter comme une défaite pour l'IA
                        if black_type == 'ai':
                            difficulty = game_data.get('black_ai_difficulty', 'medium')
                            if difficulty in stats['difficulty_stats']:
                                stats['difficulty_stats'][difficulty]['losses'] += 1
                                stats['difficulty_stats'][difficulty]['games'] += 1
                elif winner == 'black':
                    stats['black_wins'] += 1
                    if black_type == 'ai':
                        stats['ai_wins'] += 1
                        # Ajouter aux statistiques par difficulté
                        difficulty = game_data.get('black_ai_difficulty', 'medium')
                        if difficulty in stats['difficulty_stats']:
                            stats['difficulty_stats'][difficulty]['wins'] += 1
                            stats['difficulty_stats'][difficulty]['games'] += 1
                    else:
                        stats['human_wins'] += 1
                        # Si l'adversaire était une IA, compter comme une défaite pour l'IA
                        if white_type == 'ai':
                            difficulty = game_data.get('white_ai_difficulty', 'medium')
                            if difficulty in stats['difficulty_stats']:
                                stats['difficulty_stats'][difficulty]['losses'] += 1
                                stats['difficulty_stats'][difficulty]['games'] += 1
                elif game_data.get('game_over', False):
                    stats['draws'] += 1
                    # Ajouter aux statistiques par difficulté pour les deux IA si applicable
                    if white_type == 'ai':
                        difficulty = game_data.get('white_ai_difficulty', 'medium')
                        if difficulty in stats['difficulty_stats']:
                            stats['difficulty_stats'][difficulty]['draws'] += 1
                            stats['difficulty_stats'][difficulty]['games'] += 1
                    if black_type == 'ai':
                        difficulty = game_data.get('black_ai_difficulty', 'medium')
                        if difficulty in stats['difficulty_stats']:
                            stats['difficulty_stats'][difficulty]['draws'] += 1
                            stats['difficulty_stats'][difficulty]['games'] += 1
                
                # Compter les mouvements
                moves = len(game_data.get('history', []))
                stats['total_moves'] += moves
                
                # Collecter les temps de mouvement si disponibles
                if 'move_times' in game_data:
                    stats['move_times'].extend(game_data['move_times'])
                    ai_performance['move_times'].extend(game_data['move_times'])
                
                # Collecter les temps d'évaluation si disponibles
                if 'evaluation_times' in game_data:
                    ai_performance['evaluation_times'].extend(game_data['evaluation_times'])
                
                # Collecter les nœuds évalués si disponibles
                if 'nodes_evaluated' in game_data:
                    ai_performance['total_nodes_evaluated'] += game_data['nodes_evaluated']
                
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier {filename}: {e}")
    
    # Calculer les statistiques moyennes
    if stats['total_games'] > 0:
        stats['avg_moves'] = stats['total_moves'] / stats['total_games']
    
    if stats['move_times']:
        stats['avg_time_per_move'] = np.mean(stats['move_times'])
        stats['total_time'] = np.sum(stats['move_times'])
    
    if ai_performance['evaluation_times']:
        ai_performance['avg_evaluation_time'] = np.mean(ai_performance['evaluation_times'])
        ai_performance['max_evaluation_time'] = np.max(ai_performance['evaluation_times'])
        ai_performance['min_evaluation_time'] = np.min(ai_performance['evaluation_times'])
    
    if ai_performance['move_times']:
        ai_performance['avg_nodes_evaluated'] = ai_performance['total_nodes_evaluated'] / len(ai_performance['move_times'])
    
    # Calculer les taux de victoire par difficulté
    for difficulty, data in stats['difficulty_stats'].items():
        if data['games'] > 0:
            data['win_rate'] = (data['wins'] / data['games']) * 100
        else:
            data['win_rate'] = 0
    
    return render_template('ai_stats.html', stats=stats, ai_performance=ai_performance, performance_data=performance_data)

# Gestionnaire d'erreurs global pour capturer toutes les exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Erreur non gérée: {str(e)}")
    
    # Si c'est une requête AJAX, renvoyer une réponse JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/game-state') or request.path.startswith('/ai-thoughts') or request.path.startswith('/move'):
        return jsonify({
            'success': False,
            'error': 'Une erreur est survenue sur le serveur',
            'message': str(e)
        }), 500
    
    # Sinon, renvoyer une page d'erreur HTML
    return render_template('error.html', error=str(e)), 500

# Fonction pour sauvegarder périodiquement toutes les parties
def save_all_games():
    """Sauvegarde toutes les parties actives périodiquement."""
    with app.app_context():
        game_manager = GameManager.get_instance()
        game_count = len(game_manager.games)
        if game_count > 0:
            app.logger.info(f"Sauvegarde automatique de {game_count} parties...")
            game_manager.save_games()
        else:
            app.logger.info("Aucune partie à sauvegarder.")

if __name__ == '__main__':
    # Configurer la sauvegarde périodique des parties
    import threading
    import time
    
    def background_save():
        while True:
            time.sleep(300)  # Sauvegarder toutes les 5 minutes
            save_all_games()
    
    # Démarrer le thread de sauvegarde en arrière-plan
    save_thread = threading.Thread(target=background_save, daemon=True)
    save_thread.start()
    
    app.run(debug=True, host='0.0.0.0')