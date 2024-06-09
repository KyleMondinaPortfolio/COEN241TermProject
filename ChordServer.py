import socket
import pickle
import hashlib
import threading
import struct
import os
import shutil

from NetworkUtil import grab_chord_node
from ChordNode import ChordNode

PORT = 5000
M = 8

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
            # Receive the message type length
            message_type_length_data = client_socket.recv(4)
            if len(message_type_length_data) < 4:
                raise Exception("Incomplete message type length received")

            message_type_length = struct.unpack('!I', message_type_length_data)[0]

            # Receive the message type
            message_type_encoded = client_socket.recv(message_type_length)
            if len(message_type_encoded) < message_type_length:
                raise Exception("Incomplete message type received")

            message_type = message_type_encoded.decode('utf-8')

            if message_type == 'NOTIFY':
                # Receive the object length
                obj_length_data = client_socket.recv(4)
                if len(obj_length_data) < 4:
                    raise Exception("Incomplete object length received")

                obj_length = struct.unpack('!I', obj_length_data)[0]

                # Receive the actual object data
                obj_data = bytearray()
                while len(obj_data) < obj_length:
                    packet = client_socket.recv(obj_length - len(obj_data))
                    if not packet:
                        raise Exception("Incomplete object data received")
                    obj_data.extend(packet)

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
                        if not (self.node.id <= n0.id <= predecessor.id):
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
                # Respond to GRAB message
                print("GRAB")
                response_obj = self.node
                response_data = pickle.dumps(response_obj)
                response_length = struct.pack('!I', len(response_data))
                client_socket.sendall(response_length + response_data)

            elif message_type == 'PING':
                # Start sechord
                # Respond to PING message with a PONG
                print("Received PING, responding with PONG")
                response_type = "PONG"
                response_type_encoded = response_type.encode('utf-8')
                response_type_length = len(response_type_encoded)

                # Construct the data to send
                data_to_send = struct.pack('!I', response_type_length) + response_type_encoded

                # Send all data at once
                client_socket.sendall(data_to_send)
            elif message_type == 'DOWNLOAD':
                # Receive the file name length
                file_name_length_data = client_socket.recv(4)
                if len(file_name_length_data) < 4:
                    raise Exception("Incomplete file name length received")
                file_name_length = struct.unpack('!I', file_name_length_data)[0]

                # Receive the file name
                file_name_encoded = client_socket.recv(file_name_length)
                if len(file_name_encoded) < file_name_length:
                    raise Exception("Incomplete file name received")
                file_name = file_name_encoded.decode('utf-8')

                # Attempt to locate the file
                file_path = f'/tmp/czhang7/uploaded/{file_name}'
                if os.path.isfile(file_path):
                    # If file is found, send back the current node's IP
                    response_type = "FOUND"
                    response_data = self.node.ip.encode('utf-8')
                else:
                    # If not found, ask the successor
                    successor_ip = self.node.successor.ip if self.node.successor else None
                    if successor_ip:
                        # Forward the request to the successor node
                        successor_response = self.forward_download_request(successor_ip, file_name)
                        response_data = successor_response.encode('utf-8')
                        response_type = "NOT FOUND" if successor_response is None else "FOUND"
                    else:
                        response_type = "NOT FOUND"
                        response_data = b''
                # Send the response back to the client
                response_type_encoded = response_type.encode('utf-8')
                response_length = struct.pack('!I', len(response_data))
                response_type_length = struct.pack('!I', len(response_type_encoded))
                client_socket.sendall(response_type_length + response_type_encoded + response_length + response_data)
            elif message_type == 'BACKUP':
                # Receive the file name length
                file_name_length_data = client_socket.recv(4)
                if len(file_name_length_data) < 4:
                    raise Exception("Incomplete file name length received")
                file_name_length = struct.unpack('!I', file_name_length_data)[0]

                # Receive the file name
                file_name_encoded = client_socket.recv(file_name_length)
                if len(file_name_encoded) < file_name_length:
                    raise Exception("Incomplete file name received")
                file_name = file_name_encoded.decode('utf-8')

                # Add file to backup list
                self.node.add_backup_file(file_name)
                print(f"Added {file_name} to backup files on node {self.node.ip}")
            elif message_type == 'GET_UPLOADED_FILES':
                # Send the list of uploaded files
                uploaded_files_encoded = pickle.dumps(self.node.uploaded_files)
                uploaded_files_length = struct.pack('!I', len(uploaded_files_encoded))
                client_socket.sendall(uploaded_files_length + uploaded_files_encoded)
                print("Sent list of uploaded files.")
            elif message_type == 'GET_BACKUP_FILES':
                # Handle the request for backup files list
                backup_files_encoded = pickle.dumps(self.node.backup_files)
                backup_files_length = struct.pack('!I', len(backup_files_encoded))
                client_socket.sendall(backup_files_length + backup_files_encoded)
                print("Sent list of backup files.")

        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection with {client_address} closed.")


    def forward_download_request(self, ip, file_name):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, PORT))
                # Sending the DOWNLOAD command
                command = 'DOWNLOAD'
                file_name_encoded = file_name.encode('utf-8')
                command_encoded = command.encode('utf-8')
                sock.sendall(struct.pack('!I', len(command_encoded)) + command_encoded + struct.pack('!I', len(file_name_encoded)) + file_name_encoded)
                # Receiving response from successor
                response_type_length_data = sock.recv(4)
                if len(response_type_length_data) < 4:
                    raise Exception("Incomplete response type length received")
                response_type_length = struct.unpack('!I', response_type_length_data)[0]
                response_type = sock.recv(response_type_length).decode('utf-8')
                response_data_length_data = sock.recv(4)
                if len(response_data_length_data) < 4:
                    raise Exception("Incomplete response data length received")
                response_data_length = struct.unpack('!I', response_data_length_data)[0]
                response_data = sock.recv(response_data_length).decode('utf-8')
                return response_data if response_type == 'FOUND' else None
        except Exception as e:
            print(f"Error forwarding download request to {ip}: {e}")
            return None

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
                print(f"----------- Node {self.node.ip}: {self.node.id}----------------")
                if self.node.successor is None:
                    successor = 'none'
                else:
                    successor = f"Successor: {self.node.successor.id, self.node.successor.ip}"
                
                if self.node.predecessor is None:
                    predecessor = 'none'
                else:
                    predecessor = f"Predecessor: {self.node.predecessor.id, self.node.predecessor.ip}"

                print(successor)
                print(predecessor)
            elif command.lower() == 'fingers':
                self.node.print_fingers()
            elif command.lower() == "fix":
                self.node.fix_fingers()
            elif command.lower() == "reconcile":
                self.node.reconcile()
            elif command.lower().startswith('download '):
                file_name = command.split(' ', 1)[1].strip()
                print(f"Initiating download for: {file_name}")

                # Ensure the 'downloaded' directory exists
                downloaded_dir = 'downloaded'
                if not os.path.exists(downloaded_dir):
                    os.makedirs(downloaded_dir)
                    print(f"Created directory: {downloaded_dir}")

                # Attempt to start the download process
                if self.node.successor:
                    # Check if this node has the file
                    file_path = f'/tmp/czhang7/uploaded/{file_name}'
                    if os.path.isfile(file_path):
                        # If file is on the local node, copy it directly to the "downloaded/" folder
                        shutil.copy(file_path, f'downloaded/{file_name}')
                        print(f"File {file_name} is present on this node ({self.node.ip}), copied to 'downloaded/'.")
                    else:
                        # If not found, ask the successor
                        successor_ip = self.node.successor.ip if self.node.successor else None
                        if successor_ip:
                            result = self.forward_download_request(successor_ip, file_name)
                            if result:
                                print(f"File {file_name} found at node: {result}")
                                # Use SCP to download the file
                                os.system(f"scp {result}:/tmp/czhang7/uploaded/{file_name} downloaded/{file_name}")
                                print(f"Downloaded {file_name} from {result} to 'downloaded/'.")
                            else:
                                print(f"File {file_name} not found in the network.")
                        else:
                            print("No successor to query.")
                else:
                    print("This node is standalone with no successors to query.")
            elif command.lower().startswith('upload '):
                file_path = command.split(' ', 1)[1].strip()
                try:
                    # Check if the file exists
                    if not os.path.isfile(file_path):
                        print(f"File not found: {file_path}")
                        continue

                    # Copy the file to the local "uploaded" directory
                    file_name = os.path.basename(file_path)
                    local_upload_path = f'/tmp/czhang7/uploaded/{file_name}'
                    shutil.copy(file_path, local_upload_path)
                    self.node.add_uploaded_file(file_name)  # Track the uploaded file
                    print(f"File {file_name} uploaded locally to {local_upload_path}")

                    # Check if there is a successor to send the file to
                    if self.node.successor:
                        successor_ip = self.node.successor.ip
                        # Send file via SCP
                        os.system(f"scp {local_upload_path} {successor_ip}:/tmp/czhang7/uploaded/{file_name}")
                        # Notify the successor to update its backup list
                        self.notify_successor_of_backup(successor_ip, file_name)
                        print(f"File {file_name} also uploaded to successor at {successor_ip}")
                    else:
                        print("No successor found, file not backed up remotely.")

                except Exception as e:
                    print(f"Error during file upload: {e}")
            elif command.lower() == 'recover':
                self.recover_files()
                print("Recover process initiated.")
            else:
                print(f"Command received: {command}")
                # Add your command handling logic here

    def get_uploaded_files_from_node(self, node_ip):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((node_ip, PORT))
                # Send the request
                message_type = "GET_UPLOADED_FILES"
                message_type_encoded = message_type.encode('utf-8')
                message_type_length = struct.pack('!I', len(message_type_encoded))
                sock.sendall(message_type_length + message_type_encoded)

                # Wait for and receive the response
                files_length_data = sock.recv(4)
                if len(files_length_data) < 4:
                    raise Exception("Incomplete response for files length received")
                files_length = struct.unpack('!I', files_length_data)[0]
                files_data = sock.recv(files_length)
                if len(files_data) < files_length:
                    raise Exception("Incomplete response for files data received")

                uploaded_files = pickle.loads(files_data)
                return uploaded_files
        except Exception as e:
            print(f"Error retrieving uploaded files from {node_ip}: {e}")
            return []

    def get_backup_files_from_node(self, node_ip):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((node_ip, PORT))
                # Prepare and send the request
                message_type = "GET_BACKUP_FILES"
                message_type_encoded = message_type.encode('utf-8')
                message_type_length = struct.pack('!I', len(message_type_encoded))
                sock.sendall(message_type_length + message_type_encoded)

                # Receive the response
                files_length_data = sock.recv(4)
                if len(files_length_data) < 4:
                    raise Exception("Incomplete data for file list length")
                files_length = struct.unpack('!I', files_length_data)[0]
                files_data = sock.recv(files_length)
                if len(files_data) < files_length:
                    raise Exception("Incomplete data for files")

                backup_files = pickle.loads(files_data)
                return backup_files
        except Exception as e:
            print(f"Error retrieving backup files from {node_ip}: {e}")
            return []


    def notify_successor_of_backup(self, successor_ip, file_name):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((successor_ip, PORT))
                # Prepare the message
                message_type = "BACKUP"
                message_content = file_name
                message_type_encoded = message_type.encode('utf-8')
                message_content_encoded = message_content.encode('utf-8')
                message_type_length = struct.pack('!I', len(message_type_encoded))
                message_content_length = struct.pack('!I', len(message_content_encoded))
                
                # Send message type and content
                sock.sendall(message_type_length + message_type_encoded + message_content_length + message_content_encoded)
                print(f"Backup notification sent to {successor_ip} for file {file_name}")
        except Exception as e:
            print(f"Error notifying successor {successor_ip} of backup: {e}")

    def recover_files(self):
        # Recover missing uploaded files from predecessor's list
        if self.node.predecessor and self.node.predecessor.ip != self.ip:  # Ensure the predecessor is not self
            uploaded_files_list = self.get_uploaded_files_from_node(self.node.predecessor.ip)
            local_uploaded_files = [f for f in uploaded_files_list if not os.path.exists(f"/tmp/czhang7/uploaded/{f}")]
            for file_name in local_uploaded_files:
                # Request missing file from predecessor
                scp_command = f"scp {self.node.predecessor.ip}:/tmp/czhang7/uploaded/{file_name} /tmp/czhang7/uploaded/{file_name}"
                result = os.system(scp_command)
                if result == 0:  # Assuming successful SCP transfer
                    self.node.add_backup_file(file_name)
                    print(f"Successfully recovered and updated uploaded file list for {file_name}.")
                else:
                    print(f"Failed to recover uploaded file {file_name} from predecessor.")

        # Recover missing backup files from successor's list
        if self.node.successor and self.node.successor.ip != self.ip:  # Ensure the successor is not self
            backup_files_list = self.get_backup_files_from_node(self.node.successor.ip)
            missing_backup_files = [f for f in backup_files_list if not os.path.exists(f"/tmp/czhang7/uploaded/{f}")]
            for file_name in missing_backup_files:
                # Use SCP directly to request missing backup file from successor
                scp_command = f"scp {self.node.successor.ip}:/tmp/czhang7/uploaded/{file_name} /tmp/czhang7/uploaded/{file_name}"
                result = os.system(scp_command)
                if result == 0:  # Assuming successful SCP transfer
                    self.node.add_uploaded_file(file_name)
                    print(f"Successfully recovered and updated backup file list for {file_name}.")
                else:
                    print(f"Failed to recover backup file {file_name} from successor.")
