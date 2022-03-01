from typing import List, Dict
from board.board import Board, Move, PieceColor
from server_core.server_core import Server

lobby: Dict[str, str] = {}
games: Dict[int, 'Game'] = {}


class Game:
    def __init__(self, white_file_descriptor: int, black_file_descriptor: int):
        self.white_player_fd = white_file_descriptor
        self.black_player_fd = black_file_descriptor
        self._board = Board()

    def make_move(self, move: Move) -> None:
        self._board.make_move(move)

    def get_board(self) -> Board:
        return self._board

    def get_moving_player_fd(self) -> int:
        if self._board.moving_side == PieceColor.WHITE:
            return self.white_player_fd
        return self.black_player_fd

    def is_move_legal(self, move: Move) -> bool:
        captures, normal_moves = self._board.generate_moves()
        return move in captures or (len(captures) == 0 and move in normal_moves)


def handle_ping_request(args: List[str], res: Server.Response) -> None:
    res.send('pong')


def handle_host_game_request(args: List[str], res: Server.Response) -> None:
    if not len(args):
        res.reject_request()
        return
    lobby[str(res.get_file_descriptor())] = args[0]
    res.send('ok. Waiting in the lobby.')


def handle_join_game_request(args: List[str], res: Server.Response) -> None:
    if not len(args):
        res.reject_request()
        return
    game_host_file_descriptor = args[0]
    if game_host_file_descriptor not in lobby:
        res.send(f'Host with {game_host_file_descriptor} id not found')
        return
    lobby.pop(game_host_file_descriptor)
    game = Game(int(game_host_file_descriptor), res.get_file_descriptor())
    games[res.get_file_descriptor()] = game
    games[int(game_host_file_descriptor)] = game
    host_response = res.pair_with(int(game_host_file_descriptor))
    res.send(f'starting game with {game_host_file_descriptor} \n {str(game.get_board())}')
    host_response.send(f'starting game with {res.get_file_descriptor()} \n {str(game.get_board())}')


def handle_search_lobby_request(args: List[str], res: Server.Response) -> None:
    response = '\n'.join(f'{host_id} {game_name}' for host_id, game_name in lobby.items())
    res.send(response)


def handle_make_move_request(args: List[str], res: Server.Response) -> None:
    game = games.get(res.get_file_descriptor())
    if game is None:
        res.send('Game not found')
        return
    if len(args) < 1:
        res.reject_request()
        return
    if game.get_moving_player_fd() != res.get_file_descriptor():
        res.send('Not your turn')
        return
    if not Move.is_valid_move_string(args[0]):
        res.send('Invalid move format')
        return
    move = Move.from_string(args[0])
    if not game.is_move_legal(move):
        res.send('Move is illegal')
        return
    game.make_move(move)
    response = str(game.get_board())
    print(response)
    paired_response = res.get_paired_response()
    if paired_response is None:
        return
    paired_response.send(args[0])
    res.send(response)


def handle_connection_close(file_descriptor: int) -> None:
    if str(file_descriptor) in lobby:
        lobby.pop(str(file_descriptor))
    if file_descriptor in games:
        game: Game = games[file_descriptor]
        first_player, second_player = game.black_player_fd, game.white_player_fd
        del games[first_player]
        del games[second_player]


app = Server('0.0.0.0', 5000)
app.register_handler('ping', handle_ping_request)
app.register_handler('host', handle_host_game_request)
app.register_handler('join', handle_join_game_request)
app.register_handler('find_games', handle_search_lobby_request)
app.register_handler('move', handle_make_move_request)
app.set_connection_close_callback(handle_connection_close)
app.start()
