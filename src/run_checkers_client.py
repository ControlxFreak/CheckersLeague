"""
run_checkers_client.py
    - Main script for executing a local simulation with a PyGame GUI via Server Connection.

Anthony Trezza
26 Jan 2018

CHANGE LOG:
    - 1/26/2018 trezza - Software Birthday <(^.^)>
"""

from utils.jsonsocket import *
from msgs.messages import *
from players.simple_ai import SimpleAI
from board import CheckerBoard
from threading import Thread
import copy
import sys
import signal

cc = object

# TODO: Don't crash if server isn't on...


class CheckersClient:
    def __init__(self, name, host, port, player):
        self._host = host
        self._port = port
        self._name = name
        self._client = Client()

        self.player = player

        self.state = "NOT_CONNECTED"

        # Game Rules
        self._timeout = -1
        self._color = 'none'
        self._board_size = -1

        self.board = object

    def connect(self):
        # Try to connect to the server
        try:
            self._client.connect(self._host, self._port)
        except ...:
            raise Exception("Could not connect to the server...")

        print("[+] Connection established!")
        self.state = "CONNECTED"

        print("[.] Sending ConnectionRequest message...")
        # Send the connection request message
        connect_request = ConnectionRequest(self._name)
        data = dict(connect_request)

        try:
            self._client.send(data)
        except ...:
            raise Exception("Could not send the connection request message to the server...")

        print("[+] ConnectionRequest message sent and received!")

    def play(self):
        # Initialize the connection
        print("[.] Initializing Connection...")
        self.connect()

        # Loop until the game is over
        while self.state != "GAME_OVER":

            # Grab the message
            message = self._client.recv()

            # Utilize the message ID to iterate through the state machine
            if message['id'] == MESSAGE_IDS['WAITING_FOR_OPPONENT'].value and self.state == "CONNECTED":
                # The game has not started yet.  We are connected but we may or may not be waiting for an opponent to
                # join us
                w4o = WaitingForOpponent()
                w4o.from_dict(message)

                if w4o.flag is None:
                    print("[-] INVALID MESSAGE.  WaitingForOpponent Message Requires a flag")
                    continue
                elif w4o.flag is True:
                    print("[.] Waiting for opponent...")
                    continue
                else:
                    print("[+] Opponent found!")
                    self.state = "FOUND_GAME"

            elif message['id'] == MESSAGE_IDS['GAME_RULES'].value and self.state == "FOUND_GAME":
                # Wait for the rules...
                gr = GameRules()
                gr.from_dict(message)

                # Todo: error checking...

                self._color = gr.player_color
                self._timeout = gr.time_limit
                self._board_size = gr.board_size

                print("[+] Rules Received!")

                try:
                    self.board = CheckerBoard(self._board_size)
                except ...:
                    raise Exception("Could not launch the checker board")

                try:
                    self.player(self._board_size, self._timeout)
                except ...:
                    raise Exception("Could not launch AI Program")

                print("[+] Launched the AI!")
                self.state = "GAME_LAUNCHED"

            elif message['id'] == MESSAGE_IDS['BEGIN_GAME'].value and self.state == "GAME_LAUNCHED":
                bg = BeginGame()
                bg.from_dict(message)

                # TODO: More error checking...
                if bg.id != MESSAGE_IDS["BEGIN_GAME"].value:
                    raise Exception("INVALID MESSAGE")

                print("[+] Time to play!")
                self.state = "PLAYING"

            elif message['id'] == MESSAGE_IDS['YOUR_TURN'].value and self.state == "PLAYING":
                print("[+] My Turn!")
                move_list = []
                t = Thread(target=self.player.move, args=(copy.deepcopy(self.board), self._timeout, move_list))
                t.start()
                t.join(self._timeout)

                my_move = Move(move_list)
                print("[.] Playing move {}".format(move_list))
                self._client.send(dict(my_move))

            elif message['id'] == MESSAGE_IDS['MOVE'].value and self.state == "PLAYING":
                move = Move()
                move.from_dict(message)
                print("[.] Received Move {}".format(move.move_list))

                self.board.execute_move(move.move_list)

            elif message['id'] == MESSAGE_IDS['GAME_OVER'].value and self.state == "PLAYING":
                go = GameOver()
                go.from_dict(message)

                if go.winner == self._color:
                    print("[+] Victory!")
                else:
                    print("[+] Defeat!")

                self.state = "GAME_OVER"

    def shutdown(self):
        print("[-] Shutting Down...")
        self._client.close()


def signal_handler(signal, frame):
    print("[-] Ctrl+C!  Shutting down...")
    cc.shutdown()
    sys.exit(0)


def main():
    """ main()
        -  Just launches the server
    :param: void
    :return: void
    """

    # Register the crl+c signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Instantiate the game server
    cc = CheckersClient("SimpleAI", socket.gethostname(), 2004, SimpleAI)
    try:
        cc.play()
    finally:
        cc.shutdown()


if __name__ == '__main__':
    main()
