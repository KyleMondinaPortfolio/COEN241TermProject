# NetworkUtil.py
import socket
import pickle
import struct

PORT = 5000

def grab_chord_node(ip):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set the SO_REUSEADDR option to allow reuse of the address
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    client_socket.connect((ip, int(PORT)))
    
    # Send the message type with a fixed-length header
    message_type = "GRAB"
    message_type_encoded = message_type.encode('utf-8')
    message_type_length = len(message_type_encoded)
    
    # Ensure the message type length is fixed (e.g., 4 bytes for the length)
    header = struct.pack('!I', message_type_length)  # 4-byte unsigned int

    # Send header and message type
    client_socket.sendall(header + message_type_encoded)
    
    # Receive the response containing the serialized Chord node
    response_data = client_socket.recv(4096)
    chord_node = pickle.loads(response_data)
    
    client_socket.close()
    print(f"Received node from {ip}, {chord_node.ip}")
    return chord_node
