from enum import Enum
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from board.board import MoveDirections, Coordinates


class PieceType(Enum):
    PAWN = 'PAWN'
    KING = 'KING'


class PieceColor(Enum):
    WHITE = 'WHITE'
    BLACK = 'BLACK'


MOVE_DIRECTIONS: Dict[PieceType, 'MoveDirections'] = {
    PieceType.PAWN: [(1, 1), (-1, 1)],
    PieceType.KING: [(1, 1), (-1, 1), (-1, -1), (1, -1)],
}

PIECE_TO_CHAR = {
    PieceColor.WHITE: {
        PieceType.PAWN: '⛂',
        PieceType.KING: '⛃',
    },
    PieceColor.BLACK: {
        PieceType.PAWN: '⛀',
        PieceType.KING: '⛁',
    },
}


class Piece:
    def __init__(self, piece_type: PieceType, color: PieceColor, position: 'Coordinates'):
        self.type: PieceType = piece_type
        self.color: PieceColor = color
        self.position: 'Coordinates' = position

    def get_move_directions(self) -> 'MoveDirections':
        if self.type == PieceType.PAWN and self.color == PieceColor.BLACK:
            # revert direction of move for black pawns
            return list(map(lambda direction: (direction[0], -direction[1]), MOVE_DIRECTIONS[self.type]))
        return MOVE_DIRECTIONS[self.type]

    def __str__(self):
        return PIECE_TO_CHAR[self.color][self.type]
