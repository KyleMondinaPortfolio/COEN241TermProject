
import sys
from Trap import TrapServer

self_ip = sys.argv[1] 

trapServer = TrapServer(self_ip)
trapServer.start_server()