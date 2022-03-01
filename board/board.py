from typing import Tuple, Dict, List, Set
from itertools import product
from board.move import Move, MoveType
from board.piece import Piece, PieceColor, PieceType, MOVE_DIRECTIONS

# used for python type hinting
Coordinates = Tuple[int, int]
MoveDirections = List[Coordinates]
MovesTuple = Tuple[List['Move'], List['Move']]


class Board:
    def __init__(self):
        self.board: Dict[Coordinates, Piece] = {}
        self.moving_side: PieceColor = PieceColor.WHITE
        self.white_pieces: Set[Piece] = set()
        self.black_pieces: Set[Piece] = set()
        self.set_starting_position()

    @staticmethod
    def get_new_position(start: Coordinates, move_vector: Coordinates, move_length: int):
        return start[0] + move_vector[0] * move_length, start[1] + move_vector[1] * move_length

    def get_piece_moves(self, piece: Piece) -> MovesTuple:
        captures = self.find_all_captures(piece.position, piece.color)
        standard: List[Move] = []  # non-capture moves
        for direction in piece.get_move_directions():
            new_coordinates = Board.get_new_position(piece.position, direction, 1)
            if not self.is_in_board(new_coordinates) or self.board.get(new_coordinates) is not None:
                continue
            standard.append(Move(MoveType.NORMAL, [piece.position, new_coordinates]))
        return captures, standard

    def find_all_captures(self, position: Coordinates, piece_color: PieceColor, captured_pieces: Set[Piece] = set()) -> \
    List[Move]:
        """finds all captures that piece placed at `position` can make"""
        found_moves: List[Move] = []
        # captures can be made in any direction
        for direction in MOVE_DIRECTIONS[PieceType.KING]:
            captured_piece_position = Board.get_new_position(position, direction, 1)
            captured_piece = self.board.get(captured_piece_position)
            if captured_piece in captured_pieces:
                # cannot capture the same piece twice in one move
                continue
            if captured_piece is None or captured_piece.color == piece_color:
                # piece that was about to be captured has the same color as moving piece
                continue
            jump_square = Board.get_new_position(position, direction, 2)  # square where piece will land after capture
            if self.board.get(jump_square) is None and self.is_in_board(jump_square):
                captured_pieces.add(captured_piece)
                next_captures = self.find_all_captures(jump_square, piece_color, captured_pieces)
                if len(next_captures) == 0:
                    found_moves.append(Move(MoveType.CAPTURE, [position, jump_square]))
                for move in next_captures:
                    found_moves.append(Move(MoveType.CAPTURE, [position]) + move)
                captured_pieces.remove(captured_piece)
        return found_moves

    def make_move(self, move: Move):
        moved_piece = self.board[move.move_squares[0]]
        final_square = move.move_squares[-1]
        self.board.pop(moved_piece.position)
        self.board[final_square] = moved_piece
        moved_piece.position = final_square
        if move.move_type == MoveType.CAPTURE:
            # remove captured pieces from the board
            for moved_from, moved_to in zip(move.move_squares, move.move_squares[1:]):
                captured_piece_pos = ((moved_from[0] + moved_to[0]) // 2, (moved_from[1] + moved_to[1]) // 2)
                captured_piece = self.board[captured_piece_pos]
                waiting_pieces = self.white_pieces if self.moving_side == PieceColor.BLACK else self.black_pieces
                waiting_pieces.remove(captured_piece)
                self.board.pop(captured_piece_pos)
        if final_square[1] == 7 and moved_piece.color == PieceColor.WHITE:
            # promotion
            moved_piece.type = PieceType.KING
        if final_square[1] == 0 and moved_piece.color == PieceColor.BLACK:
            # promotion
            moved_piece.type = PieceType.KING
        self.moving_side = PieceColor.BLACK if self.moving_side == PieceColor.WHITE else PieceColor.WHITE

    def generate_moves(self) -> MovesTuple:
        moving_pieces = self.white_pieces if self.moving_side == PieceColor.WHITE else self.black_pieces
        capture_moves: List[Move] = []
        standard_moves: List[Move] = []  # non-captures moves
        for piece in moving_pieces:
            piece_captures, piece_standard_moves = self.get_piece_moves(piece)
            capture_moves += piece_captures
            standard_moves += piece_standard_moves
        return capture_moves, standard_moves

    def is_move_valid(self, piece: Piece, direction: Coordinates, new_coordinates: Coordinates):
        if not self.is_in_board(new_coordinates):
            # outside of the board
            return False
        if self.board.get(new_coordinates) is not None:
            if self.board[new_coordinates].color == piece.color:
                # square is already occupied by piece with the same color
                return False
        return True

    def is_in_board(self, position: Coordinates):
        return 0 <= position[0] < 8 and 0 <= position[1] < 8

    def set_starting_position(self):
        for column, row in product(range(8), range(8)):
            if row < 3 and row % 2 == column % 2:
                created_piece = Piece(PieceType.PAWN, PieceColor.WHITE, (column, row))
                self.board[column, row] = created_piece
                self.white_pieces.add(created_piece)
            if row > 4 and row % 2 == column % 2:
                created_piece = Piece(PieceType.PAWN, PieceColor.BLACK, (column, row))
                self.board[column, row] = created_piece
                self.black_pieces.add(created_piece)

    def __str__(self):
        result = ''
        for row in range(7, -1, -1):
            result += '\n'
            for column in range(8):
                piece = self.board.get((column, row))
                if piece is None:
                    result += '·' + '  '
                else:
                    result += str(piece) + '  '
        return result

    def evaluate_position(self, color: PieceColor):
        result = 0
        own_pieces = len(self.black_pieces) if color == PieceColor.BLACK else len(self.white_pieces)
        opponent_pieces = len(self.white_pieces) if color == PieceColor.BLACK else len(self.black_pieces)
        for coordinates in self.board:
            piece = self.board[coordinates]
            if piece.color == color:
                if piece.type == PieceType.KING:
                    result += 10
                else:
                    result += 5
            else:
                if piece.type == PieceType.KING:
                    result -= 10
                else:
                    result -= 5
        _, captures = self.generate_moves()
        for move in captures:
            piece = self.board[move.move_squares[0]]
            if piece.color == color:
                result += 3 * (len(move.move_squares) - 1)
            else:
                result -= 3 * (len(move.move_squares) - 1)
        return result + (own_pieces - opponent_pieces) * 1000
