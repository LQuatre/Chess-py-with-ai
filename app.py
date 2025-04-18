from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from game.game_state import GameState
from game.game_manager import GameManager
from game.game_manager import GameManager
from game.move import Move
from routes.board_routes import board_routes
from game.game import Game
import uuid
from game.game import Game
import uuid

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
        # Log the error for debugging
        app.logger.error(f"Game not found: {game_id}")
        
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
        
        # Journalisation de la requête
        app.logger.info(f"Requête de mouvement reçue: {data}")
        
        # Vérifier si les clés nécessaires sont présentes
        if 'from' in data and 'to' in data and 'game_id' in data:
            game_id = data['game_id']
            from_pos = data['from']
            to_pos = data['to']
            
            app.logger.info(f"Traitement du mouvement: {from_pos} → {to_pos} pour la partie {game_id}")
            
            game_manager = GameManager.get_instance()
            game = game_manager.get_game(game_id)
            
            if not game:
                app.logger.error(f"Partie non trouvée: {game_id}")
                return jsonify({'success': False, 'error': 'Game not found'}), 404
                
            # Exécuter le mouvement
            app.logger.info(f"Exécution du mouvement: {from_pos} → {to_pos}")
            success, message = game.play_turn(from_pos, to_pos)
            app.logger.info(f"Résultat du mouvement: {'Succès' if success else 'Échec'}, Message: {message}")
            
            # Vérifier s'il y a une promotion en attente
            promotion_pending = game.board.has_promotion_pending()
            
            # Préparer la réponse
            response = {
                'success': success,
                'message': message,
                'game_state': game.get_game_state(),
                'promotion_pending': promotion_pending
            }
            
            app.logger.info(f"Réponse préparée avec succès")
            return jsonify(response)
        
        app.logger.error(f"Données de requête invalides: {data}")
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
    game_manager = GameManager.get_instance()
    game = game_manager.get_game(game_id)
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    return jsonify(game.get_game_state())

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
    
    if game.white_ai:
        white_thoughts = game.white_ai.get_thought_log()
    
    if game.black_ai:
        black_thoughts = game.black_ai.get_thought_log()
    
    return jsonify({
        'white_player_type': game.white_player_type,
        'black_player_type': game.black_player_type,
        'white_thoughts': white_thoughts,
        'black_thoughts': black_thoughts
    })

# Supprimez cette section car elle est dupliquée plus bas dans le fichier

# Route pour consulter les parties sauvegardées
@app.route('/saved-games', methods=['GET'])
def list_saved_games():
    import os
    import json
    from datetime import datetime
    
    save_dir = os.path.join(os.path.dirname(__file__), 'saved_games')
    
    if not os.path.exists(save_dir):
        return render_template('saved_games.html', games=[])
    
    games = []
    for filename in os.listdir(save_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(save_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    game_data = json.load(f)
                    
                # Extraire les informations importantes
                game_info = {
                    'id': filename.replace('game_', '').replace('.json', ''),
                    'white_player': game_data.get('white_player_type', 'human'),
                    'black_player': game_data.get('black_player_type', 'human'),
                    'winner': game_data.get('winner', 'En cours'),
                    'timestamp': game_data.get('timestamp', ''),
                    'moves': len(game_data.get('history', [])),
                    'file_path': file_path
                }
                
                # Convertir le timestamp en format lisible
                if game_info['timestamp']:
                    try:
                        dt = datetime.fromisoformat(game_info['timestamp'])
                        game_info['date'] = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        game_info['date'] = game_info['timestamp']
                
                games.append(game_info)
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier {filename}: {e}")
    
    # Trier les parties par date (les plus récentes d'abord)
    games.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return render_template('saved_games.html', games=games)

# Route pour visualiser une partie sauvegardée
@app.route('/view-saved-game/<game_id>', methods=['GET'])
def view_saved_game(game_id):
    import os
    import json
    
    file_path = os.path.join(os.path.dirname(__file__), 'saved_games', f'game_{game_id}.json')
    
    if not os.path.exists(file_path):
        return redirect(url_for('list_saved_games'))
    
    try:
        with open(file_path, 'r') as f:
            game_data = json.load(f)
        
        # Extraire les données nécessaires pour l'affichage
        board_state = game_data.get('board', {})
        turn = game_data.get('turn', 'white')
        game_over = game_data.get('game_over', False)
        winner = game_data.get('winner', None)
        white_player_type = game_data.get('white_player_type', 'human')
        black_player_type = game_data.get('black_player_type', 'human')
        history = game_data.get('history', [])
        
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
    
    # Récupérer les statistiques des parties sauvegardées
    save_dir = os.path.join(os.path.dirname(__file__), 'saved_games')
    
    if not os.path.exists(save_dir):
        return render_template('ai_stats.html', stats={})
    
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
        'black_wins': 0
    }
    
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
                    else:
                        stats['human_wins'] += 1
                elif winner == 'black':
                    stats['black_wins'] += 1
                    if black_type == 'ai':
                        stats['ai_wins'] += 1
                    else:
                        stats['human_wins'] += 1
                elif game_data.get('game_over', False):
                    stats['draws'] += 1
                
                # Compter les mouvements
                moves = len(game_data.get('history', []))
                stats['total_moves'] += moves
                
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier {filename}: {e}")
    
    # Calculer la moyenne des mouvements
    if stats['total_games'] > 0:
        stats['avg_moves'] = stats['total_moves'] / stats['total_games']
    
    return render_template('ai_stats.html', stats=stats)

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