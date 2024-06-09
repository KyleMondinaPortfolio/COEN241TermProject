from NetworkUtil import grab_chord_node
from ChordNode import ChordNode
from ChordServer import ChordServer
import sys

self_ip = sys.argv[1] 
bootstrap_ip = "10.16.9.6"

chordServer = ChordServer(self_ip,bootstrap_ip)
chordServer.start_server()
