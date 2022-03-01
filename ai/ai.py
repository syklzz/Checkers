from board.piece import PieceColor
from board.board import Board
import math
import copy


class AI:
    def __init__(self, color: PieceColor, difficulty: int):
        self.color: PieceColor = color
        self.difficulty = difficulty

    def set_difficulty(self, difficulty: int):
        self.difficulty = difficulty

    def set_color(self, color: PieceColor):
        self.color = color

    def get_best_move(self, board: Board):
        best_move = None
        max_value = -math.inf
        capture_moves, standard_moves = board.generate_moves()
        all_moves = capture_moves if len(capture_moves) else standard_moves
        for move in all_moves:
            board_copy = copy.deepcopy(board)
            board_copy.make_move(move)
            value = self.minimax(board_copy, self.difficulty, -math.inf, math.inf, False)
            max_value = max(max_value, value)
            best_move = best_move if value < max_value else move
        assert best_move is not None
        return best_move

    def minimax(self, board: Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        if depth == 0:
            return board.evaluate_position(self.color)
        if maximizing is True:
            max_value = -math.inf
            capture_moves, standard_moves = board.generate_moves()
            all_moves = capture_moves + standard_moves
            for move in all_moves:
                board_copy = copy.deepcopy(board)
                board_copy.make_move(move)
                value = self.minimax(board_copy, depth - 1, alpha, beta, False)
                max_value = max(max_value, value)
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return max_value
        else:
            min_value = math.inf
            capture_moves, standard_moves = board.generate_moves()
            all_moves = capture_moves + standard_moves
            for move in all_moves:
                board_copy = copy.deepcopy(board)
                board_copy.make_move(move)
                value = self.minimax(board_copy, depth - 1, alpha, beta, True)
                min_value = min(min_value, value)
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return min_value
