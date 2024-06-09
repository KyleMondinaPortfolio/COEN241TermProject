from ChordServer import ChordServer
import sys
import os

directory_path = "/tmp/czhang7/uploaded"
if not os.path.exists(directory_path):
    os.makedirs(directory_path)

self_ip = sys.argv[1] 
chordServer = ChordServer(self_ip)
chordServer.start_server()
