from NetworkUtil import grab_chord_node
from ChordNode import ChordNode
from ChordServer import ChordServer
import sys

import os

directory_path = "/tmp/czhang7/uploaded"
if not os.path.exists(directory_path):
    os.makedirs(directory_path)

self_ip = sys.argv[1] 
bootstrap_ip = sys.argv[2]

chordServer = ChordServer(self_ip,bootstrap_ip)
chordServer.start_server()
