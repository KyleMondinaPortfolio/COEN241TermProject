# NetworkUtil.py
import socket
import pickle
import struct

PORT = 5000

def grab_chord_node(ip):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, PORT))

    try:
        # Send the GRAB message type
        message_type = "GRAB"
        message_type_encoded = message_type.encode('utf-8')
        message_type_length = len(message_type_encoded)
        header = struct.pack('!I', message_type_length)
        client_socket.sendall(header + message_type_encoded)

        # Receive the response length first
        response_length_data = client_socket.recv(4)
        if len(response_length_data) < 4:
            raise Exception("Incomplete response length received")
        
        response_length = struct.unpack('!I', response_length_data)[0]

        # Receive the actual response data
        response_data = bytearray()
        while len(response_data) < response_length:
            packet = client_socket.recv(response_length - len(response_data))
            if not packet:
                raise Exception("Incomplete response data received")
            response_data.extend(packet)

        chord_node = pickle.loads(response_data)

        print(f"Received node from {ip}, {chord_node.ip}")
        return chord_node

    except Exception as e:
        print(f"Error in grab_chord_node: {e}")
    finally:
        client_socket.close()
