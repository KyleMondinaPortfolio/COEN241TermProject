import socket
import pickle
import hashlib
import threading
import struct

from NetworkUtil import grab_chord_node
from ChordNode import ChordNode

PORT = 5000
M = 4

class ChordServer:
    def __init__(self, ip, bootstrap_ip=None):
        self.ip = ip
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if bootstrap_ip:
            bootstrap_node = grab_chord_node(bootstrap_ip)
            self.node = ChordNode(ip, bootstrap_node)
        else:
            self.node = ChordNode(ip) 

    def handle_client(self, client_socket, client_address):
        print(f"Connection from {client_address} has been established.")

        try:
            # Receive the header to determine the length of the message type
            header = client_socket.recv(4)
            if len(header) < 4:
                return  # Disconnected before receiving full header

            message_type_length = struct.unpack('!I', header)[0]

            # Receive the message type
            message_type = client_socket.recv(message_type_length).decode('utf-8')
            if not message_type:
                return

            print(message_type)

            if message_type == 'NOTIFY':
                obj_data = client_socket.recv(4096)
                n0 = pickle.loads(obj_data)
                print(f"Received NOTIFICATION from {client_address}: {n0.ip}")

                # Perform notification operation
                if self.node.predecessor is None:
                    self.node.predecessor = n0
                else:
                    predecessor = grab_chord_node(self.node.predecessor.ip)
                    if (predecessor.id < n0.id < self.node.id):
                        self.node.predecessor = n0
                    elif predecessor.id > self.node.id:
                        # Loop back
                        if predecessor.id < n0.id:
                            self.node.predecessor = n0
                            print(f"The notify function of {self.node.id} was called with argument {n0.id}, its predecessor is {self.node.predecessor.id}")
                            return
                    elif predecessor.id > n0.id:
                        self.node.predecessor = n0
                    elif self.node.id == predecessor.id:
                        # Grab a live copy of successor
                        successor = grab_chord_node(self.node.successor.ip)
                        self.node.predecessor = successor

                print(f"The notify function of {self.node.id} was called with argument {n0.id}, its predecessor is {self.node.predecessor.id}")

            elif message_type == 'GRAB':
                response_obj = self.node
                response_data = pickle.dumps(response_obj)
                response_length = struct.pack('!I', len(response_data))
                client_socket.sendall(response_length + response_data)

        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection with {client_address} closed.")

    def start_server(self):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, PORT))
        self.server_socket.listen(10)
        print(f"Server listening on {self.ip}:{PORT}")
        
        def accept_connections():
            while True:
                client_socket, client_address = self.server_socket.accept()
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_handler.start()

        accept_thread = threading.Thread(target=accept_connections)
        accept_thread.start()

        self.handle_user_input()

        accept_thread.join()

    def handle_user_input(self):
        while True:
            command = input("Enter command: ")
            if command.lower() == 'exit':
                print("Shutting down server...")
                self.server_socket.close()
                break
            elif command.lower() == 'stabilize':
                self.node.stabilize()
            elif command.lower() == 'info':
                if self.node.successor is None:
                    successor = 'none'
                else:
                    successor = f"{self.node.successor.id, self.node.successor.ip}"
                
                if self.node.predecessor is None:
                    predecessor = 'none'
                else:
                    predecessor = f"{self.node.predecessor.id, self.node.predecessor.ip}"

                print(successor)
                print(predecessor)
            else:
                print(f"Command received: {command}")
                # Add your command handling logic here

