import socket
import threading
import random
import time
import logging

TIMEOUT = 2  # Timeout for election in seconds
HEARTBEAT_INTERVAL = 1  # Heartbeat interval from leader
UDP_PORT = 5000  # Common port for all nodes
NODE_COUNT = 5  # Number of nodes in the simulation

# Node States
FOLLOWER = 0
CANDIDATE = 1
LEADER = 2


class Node:
    def __init__(self, node_id, other_nodes):
        self.node_id = node_id
        self.state = FOLLOWER
        self.other_nodes = other_nodes
        self.votes_received = 0
        self.vote_count = 0
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('localhost', UDP_PORT + node_id))
        self.server_socket.settimeout(TIMEOUT)
        self.leader = None
        self.running = True
        self.logger = logging.getLogger(f'Node-{self.node_id}')
        logging.basicConfig(level=logging.DEBUG)

    def send_message(self, message, addr):
        time.sleep(random.uniform(0.5, 2))
        self.server_socket.sendto(message.encode(), addr)
        self.logger.debug(f'Sent message: {message} to {addr}')

    def handle_heartbeat(self):
        while self.running:
            try:
                time.sleep(random.uniform(0.5, 2))
                data, addr = self.server_socket.recvfrom(1024)
                message = data.decode()
                if message.startswith("HEARTBEAT"):
                    self.logger.info(f'Received heartbeat from leader: {message}')
                    self.state = FOLLOWER
                    self.leader = addr
                    self.votes_received = 0
            except socket.timeout:
                if self.state == FOLLOWER:
                    self.logger.info("Heartbeat timeout, starting election.")
                    self.start_election()

    def start_election(self):
        if self.state != CANDIDATE:
            self.state = CANDIDATE
            self.votes_received = 1  # votes for himself
            self.vote_count = 0
            self.logger.info(f'Node-{self.node_id} is starting election.')
            for node in self.other_nodes:
                if node != self.node_id:
                    self.send_message(f"VOTE_REQUEST {self.node_id}", ('localhost', UDP_PORT + node))
            threading.Timer(random.uniform(1, 3), self.check_election).start()

    def check_election(self):
        if self.state == CANDIDATE and self.votes_received > len(self.other_nodes) // 2:
            self.state = LEADER
            self.logger.info(f'Node-{self.node_id} is elected as Leader.')
            self.start_heartbeat()
        elif self.state == CANDIDATE:
            self.logger.info(f'Node-{self.node_id} did not win the election, becoming follower.')
            self.state = FOLLOWER

    def start_heartbeat(self):
        while self.state == LEADER:
            time.sleep(HEARTBEAT_INTERVAL)
            for node in self.other_nodes:
                if node != self.node_id:
                    self.send_message(f"HEARTBEAT {self.node_id}", ('localhost', UDP_PORT + node))
            self.logger.debug(f'Node-{self.node_id} sending heartbeat to all followers.')

    def handle_vote_request(self, message, addr):
        if self.state == FOLLOWER:
            self.send_message(f"VOTE {self.node_id}", addr)
            self.logger.debug(f'Node-{self.node_id} votes for {message.split()[1]}.')

    def handle_vote_response(self, message):
        if message.startswith("VOTE") and self.state == CANDIDATE:
            self.votes_received += 1
            self.logger.debug(f'Node-{self.node_id} received vote.')

    def run(self):
        listener_thread = threading.Thread(target=self.handle_heartbeat)
        listener_thread.start()

        while self.running:
            try:
                data, addr = self.server_socket.recvfrom(1024)
                message = data.decode()

                if message.startswith("VOTE_REQUEST"):
                    self.handle_vote_request(message, addr)
                elif message.startswith("VOTE"):
                    self.handle_vote_response(message)
            except socket.timeout:
                continue


if __name__ == '__main__':
    nodes = [Node(i, [x for x in range(NODE_COUNT)]) for i in range(NODE_COUNT)]
    for node in nodes:
        threading.Thread(target=node.run, daemon=True).start()

    try:
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
    except KeyboardInterrupt:
        pass