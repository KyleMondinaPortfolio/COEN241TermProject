from ChordServer import ChordServer
import sys
import os

directory_path = "/tmp/$USER/uploaded"
if not os.path.exists(directory_path):
    os.makedirs(directory_path)

self_ip = sys.argv[1]
regexp_ip=re.compile("^10\.16\.9\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
regexp_name=re.compile("linux224\\d{2}")
if len(re.findall(regexp_ip,self_ip))==0 or len(re.findall(regexp_name,self_ip))==0:
    print("Invalid format of IP.")
    sys.exit(0)

chordServer = ChordServer(self_ip)
chordServer.start_server()
