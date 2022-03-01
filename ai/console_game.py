from typing import List
from ai.ai import AI
from board.piece import PieceColor
from board.board import Board, Coordinates


class Game:
    def __init__(self):
        self.board: Board = Board()
        self.difficulty = None

    def get_player_move(self):
        captures, standard = self.board.generate_moves()
        available_moves = captures if len(captures) else standard
        print("Available moves:")
        for i in range(len(available_moves)):
            sentence = ""
            for j in range(len(available_moves[i].move_squares)):
                x = str(available_moves[i].move_squares[j][0])
                y = str(available_moves[i].move_squares[j][1])
                if j == len(available_moves[i].move_squares) - 1:
                    sentence += (x + "," + y)
                else:
                    sentence += (x + "," + y + "x")
            print(sentence)
        if len(available_moves) == 0:
            return None
        while True:
            moves = input("Enter your move sentence: ")
            # Examples:
            # standard_move: 0,2x1,3
            # capture_move: 0,2x2,4x4,2
            if moves == "":
                print("Game ended!")
                exit()
            else:
                is_illegal = False
                move_coordinates: List[Coordinates] = []
                input_coordinates = moves.split("x")
                for coordinates in input_coordinates:
                    if len(coordinates.split(",")) != 2:
                        is_illegal = True
                        break
                    x_coord = coordinates.split(",")[0]
                    y_coord = coordinates.split(",")[1]
                    if not x_coord.isdigit() or not y_coord.isdigit():
                        is_illegal = True
                        break
                    move_coordinates.append((int(x_coord), int(y_coord)))
                if is_illegal:
                    print("Illegal input")
                    continue
                for i in range(len(available_moves)):
                    if available_moves[i].move_squares == move_coordinates:
                        return available_moves[i]
                print("Illegal input!")

    def start(self):
        print("Press enter if you want to end the game.")
        while True:
            answer = input("Choose difficulty [1-5]: ")
            if answer.isdigit() and 0 < int(answer) <= 5:
                self.difficulty = int(answer)
                break
            elif answer == "":
                print("Game ended!")
                exit()
            else:
                print("Illegal input!")
        while True:
            answer = input("Do you want to start? [Y/N]: ")
            if answer == "Y" or answer == "y":
                ai = AI(PieceColor.BLACK, self.difficulty)
                break
            elif answer == "N" or answer == "n":
                ai = AI(PieceColor.WHITE, self.difficulty)
                break
            elif answer == "":
                print("Game ended!")
                exit()
            else:
                print("Illegal input!")
        while True:
            print(self.board)
            if self.board.moving_side == ai.color:
                print("Opponent's turn:")
                move = ai.get_best_move(self.board)
                if move is None:
                    print("YOU WON!")
                    exit()
                self.board.make_move(move)
            else:
                print("Your turn:")
                move = self.get_player_move()
                if move is None:
                    print("YOU LOST!")
                    exit()
                self.board.make_move(move)
