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
            chordNode = self.find_successor((self.id + 2**i) % 2**M)
            self.finger_table[i] = ChordNodeRef(chordNode.id, chordNode.ip)

    def find_successor(self, id):
        # Return a live version of the successor
        if self.ping(self.successor.ip):
            successor = grab_chord_node(self.successor.ip)
        else:
            successor = self

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
            finger = self.finger_table[i]
            if finger and finger.id != self.id:
                if self.ping(finger.ip):
                    if self.id < id:
                        if self.id < finger.id < id:
                            return grab_chord_node(finger.ip)
                    else:  # Wrap around case
                        if self.id < finger.id or finger.id < id:
                            return grab_chord_node(finger.ip)
        return self

    def notify(self, target_ip, n0):
        print(f"Node {self.id} sending notification operation to {target_ip}")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((target_ip, PORT))

        try:
            # Prepare the message to send
            message_type = "NOTIFY"
            message_type_encoded = message_type.encode('utf-8')
            message_type_length = len(message_type_encoded)
            obj_data = pickle.dumps(n0)
            obj_length = len(obj_data)

            # Construct the data to send
            data_to_send = struct.pack('!I', message_type_length) + message_type_encoded
            data_to_send += struct.pack('!I', obj_length) + obj_data

            # Send all data at once
            client_socket.sendall(data_to_send)

        except Exception as e:
            print(f"Error in notify: {e}")
        finally:
            client_socket.close()

    def ping(self, target_ip):
        """Ping another node to check if it is alive."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(2)  # Set a timeout of 2 seconds

        try:
            client_socket.connect((target_ip, PORT))
            message_type = "PING"
            message_type_encoded = message_type.encode('utf-8')
            message_type_length = len(message_type_encoded)

            # Construct the data to send
            data_to_send = struct.pack('!I', message_type_length) + message_type_encoded

            # Send all data at once
            client_socket.sendall(data_to_send)

            # Wait for the response
            response_type_length_data = client_socket.recv(4)
            if len(response_type_length_data) < 4:
                raise Exception("Incomplete response type length received")

            response_type_length = struct.unpack('!I', response_type_length_data)[0]
            response_type_encoded = client_socket.recv(response_type_length)
            if len(response_type_encoded) < response_type_length:
                raise Exception("Incomplete response type received")

            response_type = response_type_encoded.decode('utf-8')
            if response_type == "PONG":
                return True
        except Exception as e:
            print(f"Error in ping: {e}")
        finally:
            client_socket.close()
        return False

    def reconcile(self):
        if not self.ping(self.successor.ip):
            print(f"Successor {self.successor.ip} is not responding. Finding a new successor.")
            self.successor = self.find_successor(self.successor.id)

        if self.predecessor and not self.ping(self.predecessor.ip):
            print(f"Predecessor {self.predecessor.ip} is not responding. Removing predecessor.")
            self.predecessor = None
        return

    def stabilize(self):
        # Periodic stabilization

        # Grab the successor and the predecessor of the successor
        if not self.ping(self.successor.ip):
            successor = self.find_successor(self.successor.id)
        elif (self.id == self.successor.id) :
            successor = self
        else:
            successor = grab_chord_node(self.successor.ip)
        
        if successor.predecessor is None:
            print("xxx")
            x_id = "None"
            x = None
        else:
            print(successor.predecessor.ip)
            x = grab_chord_node(successor.predecessor.ip)
            x_id = x.id

        print(f"Node {self.id} called the stabilize method and x is {x_id} and successor is {successor.id}")

        if x and (successor.id < self.id):
            # You are looping back
            if self.id < x.id or x.id < successor.id:
                self.successor = x
                self.notify(successor.ip, self)
                return


        if self.id == successor.id:
            print("x")
            self.successor = x
        elif successor.id < self.id:
            self.successor = successor
        elif x and (self.id < x.id < successor.id):
            print("x")
            self.successor = x
        
        
        print(f"Node {self.id} has set its successor as Node {self.successor.id}")
        self.notify(self.successor.ip, self)
    
    def print_fingers(self):
        """Print the contents of the finger table."""
        print(f"Finger table for Node {self.id}:")
        for i, finger in enumerate(self.finger_table):
            if finger:
                print(f"Finger {i}: ID - {finger.id}, IP - {finger.ip}")
            else:
                print(f"Finger {i}: None")

    def fix_fingers(self):
        # Periodically refresh finger table entries.
        print(f"fixing finger table of Node {self.id}")
        for i in range(M):
            chordNode = self.find_successor((self.id + 2**i) % 2**M)
            self.finger_table[i] = self.find_successor((self.id + 2**i) % 2**M)

        


