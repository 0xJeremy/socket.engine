from client import client
from host import host
import time
from threading import Thread

TIMEOUT = 0.5

DELAY = 5
def s(a=DELAY):
	time.sleep(a)

def report(text):
	print("\033[93m[{}]\033[0m".format(text))

def success(text):
	print("\033[32m[{}]\033[0m".format(text))


def test_connection_BOTH():
	server = host(timeout=TIMEOUT)
	server.start()
	socket = client(timeout=TIMEOUT)
	socket.start()
	report("Sockets opened and started")
	assert(server.opened)
	assert(socket.opened)
	s(0.5)
	assert(len(server.getClients()) is 1)
	report("Open state verified")
	socket.close()
	assert(not socket.opened)
	assert(socket.stopped)
	server.close()
	report("Closed state verified")
	assert(server.opened is False)
	assert(server.stopped)
	success("Connection test passed")

test_connection_BOTH()


