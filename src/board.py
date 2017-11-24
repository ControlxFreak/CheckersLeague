from players.console import ConsolePlayer
from players.simple_ai import SimpleAI
from threading import Thread
import copy
from random import choice


class CheckerBoard:
    """The CheckerBoard manages a Checkers match between two players."""
    def __init__(self, board_size):
        """Inits a CheckerBoard with the specified parameters.

        :param board_size: Size of the square board to be used. Must be even and >= 4.
        :raises ValueError: if board_size is not an even number or less than 4
        """
        if not board_size % 2 == 0:
            raise ValueError('Board size must be divisible by 2')
        if board_size < 4:
            raise ValueError("Board size must be at least 4")

        self._board_size = board_size
        self.current_player = 'w'

        """
        Build board to desired size.
        
        The board is represented by a 2D array of characters. Each element is
        either a 'b', 'B', 'w', 'W', 0, or '_'. These represent a black pawn,
        black king, white pawn, white king, empty space, or invalid space. 
        """
        self._board = []
        player_rows = (board_size / 2) - 1
        # Add white player rows
        row_ind = 0
        while row_ind < player_rows:
            row = ['_' if (j + (row_ind % 2)) % 2 == 0 else 'w' for j in range(board_size)]
            self._board.append(row)
            row_ind += 1
        # Add neutral rows
        while row_ind < player_rows + 2:
            row = ['_' if (j + (row_ind % 2)) % 2 == 0 else 0 for j in range(board_size)]
            self._board.append(row)
            row_ind += 1
        # Add black player rows
        while row_ind < board_size:
            row = ['_' if (j + (row_ind % 2)) % 2 == 0 else 'b' for j in range(board_size)]
            self._board.append(row)
            row_ind += 1

    def print(self):
        """Prints a representation of the board to the console"""
        board = '   ' + ''.join(['{:^3}'.format(i) for i in range(self._board_size)]) + '\n'
        board += '\n'.join([''.join(['{:^3}'.format(item) for item in [row_ind] + row])
                            for row_ind, row in enumerate(self._board)])
        print(board)

    def execute_move(self, move):
        """Executes specified move if valid.

        If a move is successfully executed, current_player is rotated to the next player.

        :param move: Move to execute
        :returns bool: true if move is executed successfully, false otherwise
        """
        # TODO: Check whether move is valid format
        valid_move = False
        # Create temp backup of board in case moves need to be undone
        temp_board = copy.deepcopy(self._board)
        # Group moves into pairs to handle multiple jumps
        move_pairs = [[move[i], move[i+1]] for i in range(len(move) - 1)]
        for pair in move_pairs:
            if self._validate_move(pair):
                valid_move = True
                self._board[pair[1][0]][pair[1][1]] = self._board[pair[0][0]][pair[0][1]]
                self._board[pair[0][0]][pair[0][1]] = 0
                # A pawn is promoted when it reaches the last row
                if ((pair[1][0] == self._board_size - 1 and self.current_player == 'w') or
                        (pair[1][0] == 0 and self.current_player == 'b')):
                    self._board[pair[1][0]][pair[1][1]] = self._board[pair[1][0]][pair[1][1]].upper()
                # A piece is removed if jumped over
                if abs(pair[1][0] - pair[0][0]) == 2:
                    xp = (pair[0][0] + pair[1][0]) // 2
                    yp = (pair[0][1] + pair[1][1]) // 2
                    self._board[xp][yp] = 0
            else:
                valid_move = False
                break
        if valid_move:
            # If move is valid, rotate to the next player
            self.current_player = 'w' if self.current_player == 'b' else 'b'
        else:
            # If full move was invalid, restore board to state prior to executing any moves
            self._board = temp_board
        # TODO: Log each move
        return valid_move

    def _validate_move(self, move):
        """Determines whether the move *to* location is a valid end position for piece in *from* location.

        This method generates all valid moves for the starting location in move, and then checks whether the move is in
        this set. It also checks that the piece at the starting location belongs to the current player.

        :param move: Move to validate. Tuple in form ((x1,y1),(x2,y2))
        :returns bool: true if move is valid, false otherwise
        """
        # TODO: Need to check whether any jumps are available from other pieces
        if self.current_player == self._board[move[0][0]][move[0][1]].lower():
            _, available_moves = self.generate_moves(move[0])
            return move in available_moves
        else:
            return False

    def get_winner(self):
        """Checks for end game status and returns winner.

        :returns str: 'w' if white wins, 'b' if black wins, None otherwise
        """
        # TODO: Implement other end game conditions besides no moves available
        pieces = self.get_pieces(self.current_player)
        move_count = sum([len(self.generate_moves(piece)[1]) for piece in pieces])
        if move_count == 0:
            return 'b' if self.current_player == 'w' else 'w'
        return None

    def generate_moves(self, loc, start_board=None):
        """Generates list of valid moves for the piece at loc.

        Valid moves for the piece at loc. Moves are represented as a list of locations, eg, [(x1,y1),(x2,y2)], including
        the starting location. If a board is provided, only valid jumps (not all moves) will be returned. The intention
        is a board is only provided when this is called recursively, checking for multiple jumps.

        :param loc: Location of piece to check
        :param start_board: Board to generate moves for. If not provided, current board state is used.
        :return tuple: First element is boolean indicating whether the moves are jumps or not. Second element is a list
        of location tuples which the piece at loc can move to.
        """
        jumps_only = True
        if start_board is None:
            start_board = self._board
            jumps_only = False
        moves = []
        jumps = []
        move_piece = start_board[loc[0]][loc[1]].lower()
        for step in self._generate_steps(loc, start_board):
            board = copy.deepcopy(start_board)  # create copy to test jumps on
            x, y = loc[0] + step[0], loc[1] + step[1]
            if 0 <= x < self._board_size and 0 <= y < self._board_size:
                if isinstance(board[x][y], str) and board[x][y].lower() == ('w' if move_piece == 'b' else 'b'):
                    xp, yp = x + step[0], y + step[1]
                    if (0 <= xp < self._board_size and 0 <= yp < self._board_size and
                            board[xp][yp] == 0):
                        # Move starting piece to end location
                        board[xp][yp] = board[loc[0]][loc[1]]
                        # Set starting and jumped piece to empty
                        board[loc[0]][loc[1]] = board[x][y] = 0
                        # A pawn is promoted when it reaches the last row
                        if (xp == self._board_size - 1 and move_piece == 'w') or (xp == 0 and move_piece == 'b'):
                            board[xp][yp] = board[xp][yp].upper()

                        jumps.append([loc, (xp, yp)])
                        jumps.extend([[loc] + jump_extension
                                      for jump_extension in self.generate_moves((xp, yp), board)[1]])
                elif board[x][y] == 0 and not jumps_only:
                    moves.append([loc, (x, y)])
        return (True, jumps) if len(jumps) or jumps_only > 0 else (False, moves)

    @staticmethod
    def _generate_steps(loc, board):
        char = board[loc[0]][loc[1]]
        white_steps = [(1, -1), (1, 1)]
        black_steps = [(-1, -1), (-1, 1)]
        steps = []
        if char != 'b':
            steps.extend(white_steps)
        if char != 'w':
            steps.extend(black_steps)
        return steps

    def __getitem__(self, item):
        return self._board[item]

    def get_pieces(self, w_or_b):
        """Gets a list of piece locations for the specified players.

        :param w_or_b: 'w' for white player pieces, 'b' for black player pieces. Other values invalid.
        :returns list: List of location tuples
        """
        return [(ix, iy)
                for ix, row in enumerate(self._board)
                for iy, i in enumerate(row)
                if isinstance(i, str) and i.lower() == w_or_b]


def main():
    time_limit = 1
    board_size = 8
    cb = CheckerBoard(board_size)
    players = [('w', SimpleAI(board_size, 1)), ('b', ConsolePlayer(board_size, 2))]
    move_ind = 0
    # Until end game conditions met
    while not cb.get_winner():
        player_piece, player = players[move_ind % 2]
        print('{} turn ({}):'.format(player.get_name(), 'white' if player_piece == 'w' else 'black'))
        cb.print()
        # Start a new thread to wait for Player move
        ret_val = []  # list representing move returned from player
        t = Thread(target=player.move, args=(copy.deepcopy(cb), time_limit, ret_val))
        t.start()
        t.join(time_limit)
        if not cb.execute_move(ret_val):
            print('Invalid move {} by player {}'
                  .format(ret_val, player.get_name()))
            # Choose random valid move, taking into account forced capture
            pieces = cb.get_pieces(player_piece)
            moves = []
            jumps = []
            for piece in pieces:
                is_jump, piece_moves = cb.generate_moves(piece)
                if is_jump:
                    jumps.extend(piece_moves)
                else:
                    moves.extend(piece_moves)
            move = choice(jumps) if len(jumps) > 0 else choice(moves)
            cb.execute_move(move)
            print('Playing random move instead: {}'.format(move))
        move_ind += 1
        # TODO: Log and winner
    cb.print()
    print("The winner is {}!".format(players[0 if cb.get_winner() == 'w' else 1][1].get_name()))


if __name__ == '__main__':
    main()
