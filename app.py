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
    game_manager = GameManager.get_instance()
    game_id = game_manager.create_game()
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

# Route pour obtenir l'état actuel du jeu (pour les mises à jour AJAX)
@app.route('/game-state', methods=['GET'])
def get_game_state():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({'error': 'Game ID is required'}), 400
        
    game_manager = GameManager.get_instance()
    game = game_manager.get_game(game_id)
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    return jsonify(game.get_game_state())

# Route pour effectuer un mouvement
@app.route('/move', methods=['POST'])
def make_move():
    data = request.json
    
    # Vérifier si les clés nécessaires sont présentes
    if 'from' in data and 'to' in data and 'game_id' in data:
        game_id = data['game_id']
        game_manager = GameManager.get_instance()
        game = game_manager.get_game(game_id)
        
        if not game:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
            
        # Exécuter le mouvement
        success, message = game.play_turn(data['from'], data['to'])
        
        # Vérifier s'il y a une promotion en attente
        promotion_pending = game.board.has_promotion_pending()
        
        return jsonify({
            'success': success,
            'message': message,
            'game_state': game.get_game_state(),
            'promotion_pending': promotion_pending
        })
    return jsonify({'success': False, 'error': 'Invalid request data'})

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

# Route alternative pour la compatibilité avec les anciennes URL
@app.route('/game-state/<game_id>', methods=['GET'])
def get_game_state_by_id(game_id):
    game_manager = GameManager.get_instance()
    game = game_manager.get_game(game_id)
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    return jsonify(game.get_game_state())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')