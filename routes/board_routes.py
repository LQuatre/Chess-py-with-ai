from flask import Blueprint, jsonify, render_template
from game.board import Board

board_routes = Blueprint('board_routes', __name__)

@board_routes.route('/board', methods=['GET'])
def get_board():
    """Route API pour obtenir les données du plateau au format JSON"""
    board = Board()
    return jsonify(board.to_dict())

@board_routes.route('/board/view', methods=['GET'])
def view_board():
    """Route pour afficher le plateau dans l'interface web"""
    board = Board()
    board_state = board.to_list()
    return render_template('board.html', board=board_state)