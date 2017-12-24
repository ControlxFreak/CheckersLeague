"""
server_play.py
    - Main callable method for executing a server-run simulation with a PyGame GUI.

Anthony Trezza
15 Dec 2017

CHANGE LOG:
    - 15 Dec 2017 trezza - Software's Birthday! <(^.^)>

"""

import socket
import sys
import signal
import copy
from utils import Spinner
from utils.jsonsocket import Server
from msgs.messages import *
from board_server import CheckerBoardServer

# Define the global checkers server object
gs = object


class GameServer:
    def __init__(self, tcp_port, timeout, max_games, num_players):
        """ Initializes a Game Server

        """
        # Input check

        # Initialize the input parameters
        self._tcp_port = tcp_port
        self._max_games = max_games
        self._timeout = timeout
        self._num_players = num_players

        # Create a list of our threads
        self._game_threads = []
        self._server = object
        self._spinner = object

    def open_socket(self):
        print("[+] Opening Server Socket ...")
        # Open the socket - TCP Socket Stream
        self._server = Server(socket.gethostname(), self._tcp_port, self._timeout)

    def close_socket(self):
        self._server.close()

    def run(self):
        print("[+] Running Server ...")
        # Keep accepting connections
        # Initialize a list of clients
        clients = []
        client_info = []
        num_clients = 0

        # Launch the spinner in another thread.... Just for coolness.
        self._spinner = Spinner.Spinner(self._timeout)
        self._spinner.start()
        while True:
            # Keep accepting clients until the number of players is met
            while num_clients < self._num_players:
                try:
                    client, client_addr = self._server.accept()
                except socket.timeout:
                    continue

                # Set the client's timeout to the same timeout as our own (to prevent blocking)
                client.settimeout(self._timeout)
                try:
                    # Read the message
                    msg = self._server.recv(client)

                    # Try casting that message to a connection request
                    conReq = ConnectionRequest()
                    conReq.from_dict(msg)
                    id = conReq.id
                    name = conReq.name

                    # Ensure the ID is correct
                    if id != MESSAGE_ID["CONNECTION_REQUEST"].value:
                        print("[.] Wrong Message Received.  Expected ID: " + str(MESSAGE_ID["CONNECTION_REQUEST"].value)
                              + ", RECEIVED ID: " + str(id))
                        raise Exception("Invalid Message")

                    # If the message doesn't have the name field populated from the message dictionary, this is invalid
                    if not name:
                        raise Exception("Invalid Message")

                except Exception:
                    # If any errors where thrown during when trying to read the message, return an error and close the
                    # client connection
                    print("[-] Invalid Message Received from IP Address " + str(client_addr[0]) +
                          ", Port " + str(client_addr[1]))

                    self._server.send(client, dict(ErrorMessage(ERRORS.INVALID_MSG)))
                    client.close()
                    continue

                print(type(client))
                # The message was received successfully!  Print the name
                print("[+] New Client " + name + " at IP Address " + str(client_addr[0]) +
                      ", Port " + str(client_addr[1]))
                print("[.] Num Clients: " + str(num_clients))

                # Add the new client to the current clients list
                clients.append(client)
                num_clients += 1
                if num_clients < self._num_players:
                    print("[.] Waiting for Opponent... ")
                    w4o = WaitingForOpponent(True)
                    self._server.send(client, dict(w4o))

            # Verify neither of the clients have died
            for idx, client in enumerate(clients):
                try:
                    data = self._server.recv(client)
                except socket.timeout:
                    continue

                if not data:
                    print("[-] Dead client idx " + str(idx) + " at IP address " + str(client[1][0]) + " and port " +
                          str(client[1][1]))
                    num_clients -= 1
                    conn.close_client()
                    del clients[idx]

            if len(clients) < self._num_players:
                print("[.] Not Enough Players... Still Searching...")
                continue

            # Once we have enough players, instantiate the game!
            print("[+] Starting Game!")
            w4o = WaitingForOpponent(False)
            for client in clients:
                self._server.send(client, dict(w4o))


            game = CheckerBoardServer(board_size, time_limit, clients)
            game_thread = Thread(target=game.play)
            game_thread.start()
            self._games.append(game)
            self._game_threads.append(game_thread)

    def shutdown(self):
        self.close_socket()
        self._spinner.stop()

        for game in self.games:
            game.terminate_game()

        for game_thread in self._game_threads:
            game_thread.join(self._timeout)


def signal_handler(signal, frame):
    print("[-] Ctrl+C!  Shutting down...")
    gs.shutdown()
    sys.exit(0)


def main():
    """ main()
        -  Just launches the server
    :param: void
    :return: void
    """
    global gs

    # Register the crl+c signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Instantiate the game server
    gs = GameServer(2004, 0.1, 10, 2)
    try:
        gs.open_socket()
        gs.run()
    finally:
        gs.shutdown()


if __name__ == '__main__':
    main()