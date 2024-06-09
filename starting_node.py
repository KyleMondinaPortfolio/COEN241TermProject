from ChordServer import ChordServer
import sys

self_ip = sys.argv[1] 
chordServer = ChordServer(self_ip)
chordServer.start_server()
