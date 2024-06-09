from NetworkUtil import grab_chord_node
from ChordNode import ChordNode
from ChordServer import ChordServer


print("checkpoint 1")
node = grab_chord_node("10.16.9.6")
print("checkpoint 2")
chordServer = ChordServer("127.0.0.1",node.ip)
chordServer.start_server()
