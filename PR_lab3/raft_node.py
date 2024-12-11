import socket
import threading
import time
import random
from enum import Enum


class NodeState(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3


class RaftNode:
    def __init__(self, node_id, nodes, timeout_range=(5, 10)):
        self.node_id = node_id
        self.nodes = nodes  # List of (host, port) for other nodes
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.timeout_range = timeout_range
        self.last_heartbeat = time.time()
        self.timeout = random.uniform(*self.timeout_range)
        self.votes = 0
        self.failed_nodes = set()  # Track unreachable nodes
        self.lock = threading.Lock()

        # UDP socket for communication
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("0.0.0.0", 5000 + self.node_id))

    def send_message(self, message, target):
        try:
            if target in self.failed_nodes:
                return  # Skip failed nodes
            self.socket.sendto(message.encode(), target)
        except (socket.gaierror, OSError) as e:
            print(f"Node {self.node_id}: Failed to send message to {target}: {e}")
            self.failed_nodes.add(target)  # Mark node as failed

    def broadcast_message(self, message):
        for node in self.nodes:
            self.send_message(message, node)

    def handle_message(self, message, addr):
        parts = message.split()
        cmd = parts[0]
        with self.lock:
            if cmd == "HEARTBEAT":
                self.last_heartbeat = time.time()
                if self.state != NodeState.FOLLOWER:
                    self.state = NodeState.FOLLOWER
                    print(f"Node {self.node_id} transitioned to FOLLOWER on receiving heartbeat.")
                print(f"Node {self.node_id} received heartbeat from {addr} for term {self.current_term}")
            elif cmd == "VOTE_REQUEST":
                term = int(parts[1])
                candidate_id = int(parts[2])
                if term > self.current_term and self.voted_for is None:
                    self.current_term = term
                    self.voted_for = candidate_id
                    self.send_message(f"VOTE_GRANTED {self.current_term}", addr)
                    print(f"Node {self.node_id} voted for {candidate_id} in term {term}")
            elif cmd == "VOTE_GRANTED":
                self.votes += 1
                print(f"Node {self.node_id} received vote. Total votes: {self.votes}")

    def follower_behavior(self):
        while self.state == NodeState.FOLLOWER:
            if time.time() - self.last_heartbeat > self.timeout:
                with self.lock:
                    print(f"Node {self.node_id} timeout. Starting election.")
                    self.state = NodeState.CANDIDATE

    def candidate_behavior(self):
        with self.lock:
            self.current_term += 1
            self.voted_for = self.node_id
            self.votes = 1
        self.broadcast_message(f"VOTE_REQUEST {self.current_term} {self.node_id}")
        print(f"Node {self.node_id} is a candidate in term {self.current_term}")
        start_time = time.time()
        while self.state == NodeState.CANDIDATE:
            with self.lock:
                if self.votes > len(self.nodes) // 2:
                    self.state = NodeState.LEADER
                    print(f"Node {self.node_id} became the leader for term {self.current_term}")
                    break
            if time.time() - start_time > self.timeout:
                break

    def leader_behavior(self):
        while self.state == NodeState.LEADER:
            self.broadcast_message(f"HEARTBEAT {self.current_term}")
            print(f"Node {self.node_id} (Leader) sent a heartbeat for term {self.current_term}")
            self.check_failed_nodes()
            time.sleep(1)  # Reduce interval to 1 second for quicker leader activity

    def check_failed_nodes(self):
        for node in list(self.failed_nodes):
            try:
                self.send_message("PING", node)
                print(f"Node {self.node_id}: Node {node} is reachable again.")
                self.failed_nodes.remove(node)
            except Exception:
                pass

    def run(self):
        threading.Thread(target=self.listen, daemon=True).start()
        while True:
            if self.state == NodeState.FOLLOWER:
                self.follower_behavior()
            elif self.state == NodeState.CANDIDATE:
                self.candidate_behavior()
            elif self.state == NodeState.LEADER:
                self.leader_behavior()

    def listen(self):
        while True:
            try:
                message, addr = self.socket.recvfrom(1024)
                if addr in self.failed_nodes:
                    print(f"Node {self.node_id}: Node {addr} is reachable again.")
                    self.failed_nodes.remove(addr)
                self.handle_message(message.decode(), addr)
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    node_id = int(sys.argv[1])
    # Define peers explicitly using Docker hostnames and ports
    other_nodes = [(f"node-{i}", 5000 + i) for i in range(5) if i != node_id]
    node = RaftNode(node_id, other_nodes)
    node.run()
