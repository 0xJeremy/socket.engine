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
	h = host(timeout=TIMEOUT)
	h.start()
	c = client(timeout=TIMEOUT)
	c.start()
	report("Sockets opened and started")
	assert(h.opened)
	assert(c.opened)
	s(TIMEOUT)
	assert(len(h.getClients()) is 1)
	report("Open state verified")
	c.close()
	assert(not c.opened)
	assert(c.stopped)
	h.close()
	report("Closed state verified")
	assert(not h.opened)
	assert(h.stopped)
	success("Connection test passed")
	s(1)

test_connection_BOTH()

def test_async_ordering():
	h = host(timeout=TIMEOUT, open=False)
	c = client(timeout=TIMEOUT, open=False)
	assert(not h.opened)
	h.open()
	h.start()
	assert(h.opened)
	report("Host started")
	c.open()
	# while(not c.opened):
	# 	pass
	c.start()
	assert(c.opened)
	report("Client started")
	h.close()
	assert(h.stopped)
	report("Host closed")
	c.close()
	assert(c.stopped)
	report("Client closed")
	success("Async Ordering test passed")

test_async_ordering()
