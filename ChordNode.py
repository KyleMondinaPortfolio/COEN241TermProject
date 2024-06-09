import socket
import pickle
import hashlib
import threading
import struct

from NetworkUtil import grab_chord_node

PORT = 5000
M = 4

def hash_key(key):
    """Generate a hash for a given key."""
    return int(hashlib.sha1(key.encode('utf-8')).hexdigest(), 16) % (2**M)

class ChordNodeRef:
    def __init__(self, _id, ip):
        self.id = _id
        self.ip = ip

class ChordNode:
    def __init__(self, ip, bootstrap_node = None):
        self.id = hash_key(f"{ip}:{PORT}")
        self.ip = ip
        print(f"Node with ip {self.ip} has been assigned an id of {self.id}")
        self.port = PORT
        self.successor = self
        self.predecessor = None
        self.finger_table = [ChordNodeRef(self.id, self.ip)] * M  # Assume m=160 for SHA-1
        if bootstrap_node:
            self.join(bootstrap_node)
        else:
            # Start a new P2P network if no bootstrap node is supplied
            self.initialize_first_node()

    def initialize_first_node(self):
        # Initialize this node as the first node in the network.
        self.successor = self
        self.predecessor = None
        for i in range(M):
            self.finger_table[i] = self

    def join(self, bootstrap_node):
        # Join the network using the bootstrap node.
        self.predecessor = None
        self.successor = bootstrap_node.find_successor(self.id)
        print(f"Node {self.id} called Join. its successor is Node {self.successor.id}")

        # Stabilize the joining node
        self.stabilize()

        # Initialize finger table
        for i in range(M):
            self.finger_table[i] = self.find_successor((self.id + 2**i) % 2**M)

    def find_successor(self, id):
        # Return a live version of the successor
        successor = grab_chord_node(self.successor.ip)

        # Grab the successor node
        if self.id < id < successor.id or self.id == successor.id:
            return successor
        else:
            n0 = self.closest_preceding_node(id)
            if n0.id == self.id:
                return successor
            return n0.find_successor(id)

    def closest_preceding_node(self, id):
        for i in range(M-1, -1, -1):
            if self.id < self.finger_table[i].id < id:
                chord_node = grab_chord_node(self.finger_table[i].ip)
        return self

    def notify(self, target_ip, n0):
        print(f"Node {self.id} sending notification operation to {target_ip}")
        # Connect to target_ip
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((target_ip, PORT))
        
        # Send the notification message and attach the supplied node
        message_type = "NOTIFY"
        message_type_encoded = message_type.encode('utf-8')
        message_type_length = len(message_type_encoded)
        
        # Ensure the message type length is fixed (e.g., 8 bytes)
        header = struct.pack('!I', message_type_length)  # 4-byte unsigned int

        # Send header and message type
        client_socket.sendall(header + message_type_encoded)

        # Send the serialized object
        obj_data = pickle.dumps(n0)
        client_socket.sendall(obj_data)

        client_socket.close()

    def stabilize(self):
        # Periodic stabilization

        # Grab the successor and the predecessor of the successor
        successor = grab_chord_node(self.successor.ip)
        if successor.predecessor is None:
            x_id = "None"
            x = None
        else:
            x = grab_chord_node(successor.predecessor.ip)
            x_id = x.id

        print(f"Node {self.id} called the stabilize method and x is {x_id} and successor is {successor.id}")

        if x and (successor.id < self.id):
            # You are looping back
            if self.id < x.id or x.id < successor.id:
                self.successor = x
                notify(successor.ip, self)
                return


        if self.id == successor.id:
            self.successor = x
        elif successor.id < self.id:
            self.successor = successor
        elif x and (self.id < x.id < successor.id):
            self.successor = x
        
        
        print(f"Node {self.id} has set its successor as Node {successor.id}")
        self.notify(successor.ip, self)

    def fix_fingers(self):
        # Periodically refresh finger table entries.
        print(f"fixing finger table of Node {self.id}")
        for i in range(M):
            self.finger_table[i] = self.find_successor((self.id + 2**i) % 2**M)

        


