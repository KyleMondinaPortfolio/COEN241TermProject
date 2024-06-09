import socket
import pickle
import hashlib
import threading
import struct
from statistics import mean, stdev
from NetworkUtil import grab_chord_node

PORT = 5000
M = 8
ALPHA = 1

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
        self.blacklist = set() # To keep track of blacklisted nodes
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
    
    def verify_hop(self, n0, n1, id):
        """Verify if the hop between n0 and n1 is valid."""
        nodes = [n0.id, n1.id, id]
        distances = [abs(nodes[i] - nodes[i+1]) for i in range(len(nodes)-1)]
        avg_distance = mean(distances)
        std_dev = stdev(distances)
        threshold = avg_distance + ALPHA * std_dev
        return all(d <= threshold for d in distances)

    def find_successor(self, id):
        current = self
        path = []

        while True:
            if current.id == id or current.id == self.successor.id:
                print("case A") 
                # Node is alone in the network, its successor is itself
                return current.successor

            if current.id < id <= current.successor.id or \
               (current.id > current.successor.id and (id > current.id or id <= current.successor.id)):
                print("case B") 
                if not self.ping(current.successor.ip):
                    path.append((current, self.closest_preceding_node(id)))
                    current.successor = self.closest_preceding_node(id)
                    break
                path.append((current, current.successor))
                current.successor = current.successor
                break

            next_node = current.closest_preceding_node(id)

            if next_node.id == current.id:
                # We've looped back to the same node, which means no further lookup is possible.
                print("case C") 
                path.append(current, current.successor)
                break

            if self.ping(next_node.ip):
                path.append((current, next_node))
                current = grab_chord_node(next_node.ip)
            else:
                # The next node is not responding, blacklist and continue the search
                self.blacklist.add(next_node.ip)
                print(f"Node {next_node.ip} blacklisted during routing from {current.id} to {id}")

        for n0, n1 in path:
            if not self.verify_hop(n0, n1, id):
                self.blacklist.add(n1.ip)
                print(f"Node {n1.ip} blacklisted during routing from {n0.id} to {id}")
                print("Case d")
                return self.find_successor(id)  # Retry the lookup

        return current.successor

    def closest_preceding_node(self, id):
        for i in range(M-1, -1, -1):
            finger = self.finger_table[i]
            if finger and finger.id != self.id and finger.ip not in self.blacklist:
                if self.ping(finger.ip):
                    node = grab_chord_node(finger.ip)
                    # Check if the node's id is between self.id and id
                    if self.id < id:
                        if self.id < node.id < id:
                            print(f"result of closest procceding node: {self.id} is {node.id}")
                            return node
                    else:  # Wrap around case
                        if self.id < node.id or node.id < id:
                            print(f"result of closest procceding node: {self.id} is {node.id}")
                            return node
        print(f"failure, returning self {self.id}")
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
            print(f"Resulting sucessor is {self.successor.id}")

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

        


