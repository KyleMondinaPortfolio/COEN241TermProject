import socket
from globals import PORT, M, ALPHA
from ChordNode import ChordNode
from ChordServer import ChordServer

class TrapNode(ChordNode):
    def __init__(self, ip, bootstrap_node=None):
        super().__init__(ip, bootstrap_node)
        self.evil = True  # Set the node as malicious
        self.id = 64
        self.trap = self
        print(f"Just kidding, trap node id is {self.id}")

class TrapServer(ChordServer):
    def __init__(self, ip, bootstrap_ip=None):
        self.ip = ip
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if bootstrap_ip:
            bootstrap_node = grab_chord_node(bootstrap_ip)
            self.node = TrapNode(ip, bootstrap_node)  # Initialize with a MaliciousChordNode
        else:
            self.node = TrapNode(ip)  # Initialize with a MaliciousChordNode

    def handle_client(self, client_socket, client_address):
        print(f"{client_address} FELL FOR THE TRAP!")
        super().handle_client(client_socket, client_address)  # Call the original handle_client method
