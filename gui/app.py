import pygame
from typing import Tuple, Callable, Any, Optional, List
from ai.ai import AI
from board.board import Board, Coordinates, Move
from board.piece import PieceColor, PieceType
from gui.networking import NetworkThread

Color = Tuple[int, int, int]

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (128, 0, 0)
GREY = (128, 128, 128)
DARK_BROWN = (117, 88, 71)
LIGHT_BROWN: Color = (234, 210, 172)
timer_height = 25
width = 550
height = 550 + 2 * timer_height
square_size = int(width / 8) + 1
font = 'freesansbold.ttf'
clock = pygame.time.Clock()


class App:
    def __init__(self, width: int, height: int):
        self.board: Board = Board()
        self.player_side = PieceColor.WHITE
        self.piece = None
        self.moves = []
        self.ai = AI(PieceColor.BLACK, 1)
        self.window: Any = pygame.display.set_mode((width, height))
        self.set_window()
        self.draw_current_screen: Callable[[], None] = self.main_menu
        self.should_stop = False
        self.active_difficulty = True
        self.white_time_spent = 0
        self.black_time_spent = 0
        self.network_thread = NetworkThread()
        self.user_input = ''
        self.active_input = False
        self.input_rect = pygame.Rect(int((width - 200) / 2), 200, 200, 32)
        self.list_start_index = 0
        self.lobby_index = 0
        self.lobbies: List[str] = []
        self.has_created_game: bool = False

    def restart(self):
        self.has_created_game = False
        self.board = Board()
        self.piece = None
        self.black_time_spent = 0
        self.white_time_spent = 0
        self.user_input = ''
        self.active_input = False
        self.lobby_index = 0
        self.list_start_index = 0
        self.input_rect = pygame.Rect(int((width - 200) / 2), 200, 200, 32)
        self.get_update_screen_action(self.main_menu)()
        self.network_thread.disconnect()

    def update_time(self):
        time = clock.tick(15)
        if self.draw_current_screen != self.singleplayer_game and self.draw_current_screen != self.multiplayer_game:  # type: ignore
            return
        if self.board.moving_side == PieceColor.WHITE:
            self.white_time_spent += time
        else:
            self.black_time_spent += time

    def set_window(self):
        pygame.init()
        pygame.display.set_caption("CHECKERS")

    def get_piece_coordinates(self, position: Coordinates):
        x = int(position[0] / square_size)
        y = int((position[1] - timer_height) / square_size)
        if self.player_side == PieceColor.WHITE:
            y = 7 - y
        else:
            x = 7 - x
        return [x, y]

    def get_piece_position(self, position: Coordinates):
        if self.player_side == PieceColor.WHITE:
            x = position[0]
            y = 7 - position[1]
        else:
            x = 7 - position[0]
            y = position[1]
        return [int(x * square_size + square_size / 2), int(y * square_size + square_size / 2) + timer_height]

    def format_text(self, message: str, text_font: str, text_size: int, text_color: Color):
        new_font: Any = pygame.font.Font(text_font, text_size)
        new_text = new_font.render(message, False, text_color)
        return new_text

    def button(self, text: str, x: int, y: int, width: int, height: int, inactive_color: Color, active_color: Color,
               action: Optional[Callable[[], None]]):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed(5)
        if x + width > mouse[0] > x and y + height > mouse[1] > y:
            pygame.draw.rect(self.window, active_color, (x, y, width, height))
            if click[0] == 1 and action is not None:
                action()
        else:
            pygame.draw.rect(self.window, inactive_color, (x, y, width, height))
        button_text = self.format_text(text, font, 20, WHITE)
        text_rect = button_text.get_rect()
        text_rect.center = (int(x + (width / 2)), int(y + (height / 2)))
        self.window.blit(button_text, text_rect)

    def draw_pieces(self):
        if self.piece is not None and self.piece.position in self.board.board:
            piece_position = self.moves[-1] if len(self.moves) else self.piece.position
            pygame.draw.circle(self.window, RED, self.get_piece_position(piece_position), int(square_size / 2))
            if self.player_side == self.board.moving_side:
                captures, standard = self.board.get_piece_moves(self.piece)
                all_moves = captures if len(captures) else standard
                # if there is a possible capture it has to be played
                if len(self.board.generate_moves()[0]):
                    all_moves = captures
                all_moves = filter(lambda m: m.move_squares[:len(self.moves)] == self.moves, all_moves)
                for move in all_moves:
                    pygame.draw.circle(self.window, RED, self.get_piece_position(move.move_squares[len(self.moves)]),
                                       square_size // 20)

        for piece in self.board.white_pieces:
            piece_position = self.moves[-1] if piece is self.piece and len(self.moves) else piece.position
            x, y = self.get_piece_position(piece_position)
            if piece.type == PieceType.KING:
                pygame.draw.circle(self.window, WHITE, (x, y), int(square_size / 2) - 2)
                pygame.draw.circle(self.window, RED, (x, y), int(square_size / 3) - 2)
            else:
                pygame.draw.circle(self.window, WHITE, (x, y), int(square_size / 2) - 2)
        for piece in self.board.black_pieces:
            piece_position = self.moves[-1] if piece is self.piece and len(self.moves) else piece.position
            x, y = self.get_piece_position(piece_position)
            if piece.type == PieceType.KING:
                pygame.draw.circle(self.window, BLACK, (x, y), int(square_size / 2) - 2)
                pygame.draw.circle(self.window, RED, (x, y), int(square_size / 3) - 2)
            else:
                pygame.draw.circle(self.window, BLACK, (x, y), int(square_size / 2) - 2)

    def draw_board(self):
        self.window.fill(DARK_BROWN)
        for row in range(8):
            for col in range(row % 2, 8, 2):
                pygame.draw.rect(self.window, LIGHT_BROWN,
                                 (row * square_size, col * square_size + timer_height, square_size, square_size))
        self.draw_pieces()
        pygame.draw.rect(self.window, GREY, (0, 0, width, timer_height))
        pygame.draw.rect(self.window, GREY, (0, height - timer_height, width, timer_height))

    def start(self):
        while not self.should_stop:
            self.draw_current_screen()
            pygame.display.update()
            self.update_time()

    def main_menu(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        self.window.fill(LIGHT_BROWN)

        def handle_multiplayer_clicked():
            self.draw_current_screen = self.multiplayer_menu
            self.network_thread.connect()

        self.button("SINGLE PLAYER", int(width / 4), 100, int(width / 2), 100, BLACK, RED,
                    self.get_update_screen_action(self.singleplayer_menu))
        self.button("MULTI PLAYER", int(width / 4), 300, int(width / 2), 100, BLACK, RED, handle_multiplayer_clicked)

    def get_update_screen_action(self, draw_current_screen: Callable[[], None]):
        def callback():
            self.draw_current_screen = draw_current_screen

        return callback

    def multiplayer_menu(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.restart()

        def join_action():
            self.network_thread.send_request('find_games', [])
            self.draw_current_screen = self.join_menu

        self.window.fill(LIGHT_BROWN)
        self.button("HOST", int(width / 4), 100, int(width / 2), 100, BLACK, RED,
                    self.get_update_screen_action(self.host_menu))
        self.button("JOIN", int(width / 4), 300, int(width / 2), 100, BLACK, RED, join_action)

    def host_menu(self):
        active_color = RED
        passive_color = BLACK
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.input_rect.collidepoint(event.pos):
                    self.active_input = True
                else:
                    self.active_input = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.restart()
                if self.active_input:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_input = self.user_input[:-1]
                    else:
                        self.user_input += event.unicode
            if event.type == pygame.USEREVENT:
                print(event)
                if event.name == 'host':
                    self.network_thread.wait_for_response('other_player_joined')
                if event.name == 'other_player_joined':
                    self.draw_current_screen = self.multiplayer_game
        self.window.fill(LIGHT_BROWN)
        if self.active_input:
            color = active_color
        else:
            color = passive_color

        def host_request():
            self.has_created_game = True
            self.player_side = PieceColor.WHITE
            self.network_thread.send_request('host', [self.user_input])

        if not self.has_created_game:
            label_text = self.format_text('LOBBY NAME', font, 20, BLACK)
            label_rect = label_text.get_rect()
            pygame.draw.rect(self.window, color, self.input_rect, 2)
            input_text = self.format_text(self.user_input, font, 20, BLACK)
            self.window.blit(input_text, (self.input_rect.x + 5, self.input_rect.y + 5))
            self.input_rect.w = max(input_text.get_width() + 20, 200)
            self.input_rect.x = int((width - self.input_rect.w) / 2)
            self.button("CREATE", int((width - 200) / 2), 250, 200, 50, BLACK, RED, host_request)
        else:
            label_text = self.format_text('WAITING FOR OTHER PLAYER...', font, 20, BLACK)
            label_rect = label_text.get_rect()
        self.window.blit(label_text, (int(width / 2 - (label_rect[2] / 2)), 150))

    def join_menu(self):
        lobbies = list(map(lambda l: l.split(' ', 1), self.lobbies))
        size = min(6, len(lobbies))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.restart()
                if event.key == pygame.K_DOWN:
                    if self.lobby_index + 1 < len(lobbies):
                        if self.lobby_index + 1 >= self.list_start_index + size:
                            self.list_start_index += 1
                        self.lobby_index += 1
                if event.key == pygame.K_UP:
                    if self.lobby_index - 1 >= 0:
                        if self.lobby_index - 1 < self.list_start_index:
                            self.list_start_index -= 1
                        self.lobby_index -= 1
            if event.type == pygame.USEREVENT:
                print(event)
                if event.name == 'find_games':
                    games = event.data.split('\n')
                    games.pop()
                    games.pop()  # remove 2 last empty entires created by \n\n at the end of server response
                    if games[0] == '':
                        games = []
                    self.lobbies = games
                if event.name == 'join':
                    self.network_thread.wait_for_response('other_player_move')
                    self.draw_current_screen = self.multiplayer_game
        self.window.fill(LIGHT_BROWN)
        label_text = self.format_text('LOBBIES', font, 30, BLACK)
        label_rect = label_text.get_rect()
        self.window.blit(label_text, (int(width / 2 - (label_rect[2] / 2)), 50))
        pygame.draw.rect(self.window, WHITE, (0, 110, width, 350))
        for i in range(size):
            index = self.list_start_index + i
            if index == self.lobby_index:
                server_text = self.format_text("> " + lobbies[index][1] + " <", font, 20, RED)
                server_rect = server_text.get_rect()
            else:
                server_text = self.format_text(lobbies[index][1], font, 20, BLACK)
                server_rect = server_text.get_rect()
            self.window.blit(server_text, (int(width / 2 - (server_rect[2] / 2)), 150 + i * 50))

        def join_request():
            self.player_side = PieceColor.BLACK
            self.network_thread.send_request('join', [lobbies[self.lobby_index][0]])

        self.button("JOIN", int((width - 200) / 2), 500, 200, 50, BLACK, RED, join_request)

    def singleplayer_menu(self):
        difficulty = [1, 2, 3]
        selected_difficulty = self.ai.difficulty - 1
        color = [PieceColor.WHITE, PieceColor.BLACK]
        selected_color = 1 if self.ai.color == PieceColor.WHITE else 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.restart()
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    self.active_difficulty = not self.active_difficulty
                elif event.key == pygame.K_LEFT:
                    if self.active_difficulty:
                        selected_difficulty = (selected_difficulty + len(difficulty) - 1) % len(difficulty)
                        self.ai.set_difficulty(difficulty[selected_difficulty])
                    else:
                        self.ai.set_color(color[selected_color])
                        selected_color = (selected_color + len(color) - 1) % len(color)
                        self.player_side = color[selected_color]
                elif event.key == pygame.K_RIGHT:
                    if self.active_difficulty:
                        selected_difficulty = (selected_difficulty + 1) % len(difficulty)
                        self.ai.set_difficulty(difficulty[selected_difficulty])
                    else:
                        self.ai.set_color(color[selected_color])
                        selected_color = (selected_color + 1) % len(color)
                        self.player_side = color[selected_color]
        self.window.fill(LIGHT_BROWN)
        difficulty_label = self.format_text("PICK DIFFICULTY:", font, 30, BLACK)
        color_label = self.format_text("PICK SIDE:", font, 30, BLACK)
        text = "WHITE" if color[selected_color] == PieceColor.WHITE else "BLACK"
        if self.active_difficulty:
            difficulty_text = self.format_text("<  " + str(difficulty[selected_difficulty]) + "  >", font, 25, RED)
            color_text = self.format_text("<  " + text + "  >", font, 25, BLACK)
        else:
            difficulty_text = self.format_text("<  " + str(difficulty[selected_difficulty]) + "  >", font, 25, BLACK)
            color_text = self.format_text("<  " + text + "  >", font, 25, RED)
        difficulty_label_rect = difficulty_label.get_rect()
        difficulty_rect = difficulty_text.get_rect()
        color_label_rect = color_label.get_rect()
        color_rect = color_text.get_rect()
        self.window.blit(difficulty_label, (int(width / 2 - (difficulty_label_rect[2] / 2)), 50))
        self.window.blit(difficulty_text, (int(width / 2 - (difficulty_rect[2] / 2)), 100))
        self.window.blit(color_label, (int(width / 2 - (color_label_rect[2] / 2)), 150))
        self.window.blit(color_text, (int(width / 2 - (color_rect[2] / 2)), 200))
        self.button("PLAY", int(width / 4), 350, int(width / 2), 100, DARK_BROWN, BLACK,
                    self.get_update_screen_action(self.singleplayer_game))

    def perform_player_action(self, mouse: Any, is_multiplayer: bool = False):
        x, y = self.get_piece_coordinates(mouse)
        if (x, y) in self.board.board.keys():
            if self.board.board[(x, y)].color == self.player_side:
                self.piece = self.board.board[(x, y)]
                self.moves = [(x, y)]
        elif self.piece is not None:
            captures, standard = self.board.get_piece_moves(self.piece)
            all_moves = captures if len(captures) else standard
            if len(self.board.generate_moves()[0]):
                all_moves = captures
            if (x, y) in map(lambda m: m.move_squares[len(self.moves)],
                             filter(lambda m: len(m.move_squares) > len(self.moves), all_moves)):
                self.moves.append((x, y))
                for i in range(len(all_moves)):
                    if all_moves[i].move_squares == self.moves:
                        if is_multiplayer:
                            self.network_thread.send_request('move', [str(all_moves[i])])
                            self.network_thread.wait_for_response('other_player_move')
                        self.update_time()
                        self.board.make_move(all_moves[i])
                        self.piece = None
                        self.moves = []
                        break

    def get_time(self, is_player: bool):
        time_spent = 0
        if is_player:
            time_spent = self.white_time_spent if self.player_side == PieceColor.WHITE else self.black_time_spent
        else:
            time_spent = self.black_time_spent if self.player_side == PieceColor.WHITE else self.white_time_spent
        seconds_left = (5 * 60 * 1000 - time_spent) // 1000
        seconds_string = str(seconds_left % 60)
        if seconds_left % 60 < 10:
            seconds_string = '0' + seconds_string
        return f'{seconds_left // 60}:{seconds_string}'

    def is_out_of_time(self):
        time_spent = 0
        is_player = True if self.player_side == self.board.moving_side else False
        if is_player:
            time_spent = self.white_time_spent if self.player_side == PieceColor.WHITE else self.black_time_spent
        else:
            time_spent = self.black_time_spent if self.player_side == PieceColor.WHITE else self.white_time_spent
        return 5 * 60 * 1000 - time_spent <= 0

    def singleplayer_game(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.restart()
        captures, standard = self.board.generate_moves()
        if (len(captures) == 0 and len(standard) == 0) or self.is_out_of_time():
            self.draw_current_screen = self.ending_screen
            return
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed(5)
        if click[0] == 1 and self.board.moving_side == self.player_side:
            self.perform_player_action(mouse)
        elif self.board.moving_side == self.ai.color:
            ai_move = self.ai.get_best_move(self.board)
            self.update_time()
            self.board.make_move(ai_move)
        self.draw_board()
        bot_timer = self.format_text(str(self.get_time(False)), font, 20, WHITE)
        text_rect = bot_timer.get_rect()
        text_rect.center = (width // 2, timer_height // 2)
        self.window.blit(bot_timer, text_rect)
        player_timer = self.format_text(str(self.get_time(True)), font, 20, WHITE)
        text_rect = player_timer.get_rect()
        text_rect.center = (width // 2, height - timer_height // 2)
        self.window.blit(player_timer, text_rect)

    def multiplayer_game(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.USEREVENT:
                if event.name == 'other_player_move':
                    move = Move.from_string(event.data)
                    self.update_time()
                    self.board.make_move(move)
        captures, standard = self.board.generate_moves()
        if (len(captures) == 0 and len(standard) == 0) or self.is_out_of_time():
            self.draw_current_screen = self.ending_screen
            return
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed(5)
        if click[0] == 1 and self.board.moving_side == self.player_side:
            self.perform_player_action(mouse, True)
        self.draw_board()
        opponent_timer = self.format_text(str(self.get_time(False)), font, 20, WHITE)
        text_rect = opponent_timer.get_rect()
        text_rect.center = (width // 2, timer_height // 2)
        self.window.blit(opponent_timer, text_rect)
        player_timer = self.format_text(str(self.get_time(True)), font, 20, WHITE)
        text_rect = player_timer.get_rect()
        text_rect.center = (width // 2, height - timer_height // 2)
        self.window.blit(player_timer, text_rect)

    def ending_screen(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.restart()
        self.window.fill(LIGHT_BROWN)
        result = "YOU LOST!" if self.player_side == self.board.moving_side else "YOU WON!"
        text = self.format_text(result, font, 40, BLACK)
        text_rect = text.get_rect()
        self.window.blit(text, (int(width / 2 - (text_rect[2] / 2)), 200))
