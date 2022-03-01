import re
from enum import Enum
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from board.board import Coordinates


class MoveType(Enum):
    CAPTURE = 'CAPTURE'
    NORMAL = 'NORMAL'


class Move:
    def __init__(self, move_type: MoveType, move_squares: List['Coordinates']):
        self.move_squares = move_squares
        self.move_type = move_type

    @staticmethod
    def is_valid_move_string(move_string: str) -> bool:
        numbers_from_1_to_32 = '(?:[1-9]|(?:[1-2]\\d)|(?:3[0-2]))'
        standard_move = f'(?:{numbers_from_1_to_32}-{numbers_from_1_to_32})'  # ex 24-20
        capture_move = f'(?:(?:{numbers_from_1_to_32}x)+{numbers_from_1_to_32})'  # ex 23x14x5
        pattern = f'^(?:{standard_move}|{capture_move})$'
        if re.match(pattern, move_string) is None:
            return False
        return True

    @classmethod
    def from_string(cls, move_string: str) -> 'Move':
        def square_id_to_coordinates(square_id_string: str) -> 'Coordinates':
            square_id = int(square_id_string)
            y = 7 - (square_id - 1) // 4
            x = (square_id - 1) % 4 * 2 + (y % 2)
            return x, y

        move_squares = move_string.split('-')
        if len(move_squares) == 2:
            moves_list = list(map(square_id_to_coordinates, move_squares))
            return cls(MoveType.NORMAL, moves_list)
        else:
            move_squares = move_string.split('x')
            moves_list = list(map(square_id_to_coordinates, move_squares))
            return cls(MoveType.CAPTURE, moves_list)

    def __str__(self) -> str:
        # Standard checkers move notation, each reachable square has number from 1-32 assigned to it,
        # starting from top left. Move is written as numbers of squares that moving piece has reached 
        # separated by `-` if move was a normal move and with `x` for captures. Ex. 9-14 or 22x15x24.
        move_str = ''
        for square in self.move_squares:
            square_id = (-square[1] + 7) * 4 + (square[0] // 2) + 1
            move_str += str(square_id)
            move_str += 'x' if self.move_type == MoveType.CAPTURE else '-'
        move_str = move_str[:-1]
        return move_str

    def __add__(self, other: object) -> 'Move':
        if isinstance(other, self.__class__):
            self.move_squares += other.move_squares
        return self

    def __hash__(self) -> int:
        return hash((tuple(self.move_squares), self.move_type))

    def __eq__(self, move: object) -> bool:
        if not isinstance(move, Move):
            return False
        return move.move_squares == self.move_squares and move.move_type == self.move_type

    def __ne__(self, move: object) -> bool:
        if not isinstance(move, Move):
            return True
        return move.move_squares != self.move_squares or move.move_type != self.move_type
