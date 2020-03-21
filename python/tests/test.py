#!/usr/bin/env python3

from socketengine import client
from socketengine import host
import time
import argparse

TIMEOUT = 0.5
DELAY = 0.5
DEBUG = False

########################
### HELPER FUNCTIONS ###
########################

def s(a=DELAY):
	time.sleep(a)

def report(text):
	global DEBUG
	if DEBUG:
		print("\033[93m[{}]\033[0m".format(text))

def success(text):
	print("\033[32m[{}]\033[0m".format(text))
	s(1)

def initialize():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	report("Sockets initialized")
	h.start()
	c.start()
	report("Sockets started")
	return h, c


text = "Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor match. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. "

##################
### UNIT TESTS ###
##################

def test_connection_BOTH():
	start = time.time()
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
	assert(not c.opened and c.stopped)
	assert(c.stopped)
	h.close()
	report("Closed state verified")
	assert(not h.opened and h.stopped)
	success("Connection test Passed ({:.5f} sec)".format(time.time()-start))

def test_async_ordering():
	start = time.time()
	h = host(timeout=TIMEOUT, open=False)
	c = client(timeout=TIMEOUT, open=False)
	assert(not h.opened)
	h.open()
	h.start()
	assert(h.opened)
	report("Host started")
	c.open()
	c.start()
	assert(c.opened)
	report("Client started")
	h.close()
	assert(h.stopped)
	report("Host closed")
	c.close()
	assert(c.stopped)
	report("Client closed")
	success("Async Ordering test Passed ({:.5f} sec)".format(time.time()-start))

def test_empty_message():
	start = time.time()
	h, c = initialize()
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	assert(h.get_ALL("Test") == [])
	assert(h.get_ALL("Test2") == [])
	c.close()
	h.close()
	success("Empty messages test Passed ({:.5f} sec)".format(time.time()-start))

def test_host_messages():
	start = time.time()
	h, c = initialize()
	assert(h.get_ALL("Test") == [])
	assert(h.get_ALL("Test2") == [])
	c.write("Test", "test of port 1")
	s()
	assert(h.get_ALL("Test") == ["test of port 1"])
	assert(h.get_ALL("Test2") == [])
	c.write("Test2", "test of port 2")
	s()
	assert(h.get_ALL("Test") == ["test of port 1"])
	assert(h.get_ALL("Test2") == ["test of port 2"])
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	c.close()
	h.close()
	success("Client -> Host Passed ({:.5f} sec)".format(time.time()-start))

def test_client_messages():
	start = time.time()
	h, c = initialize()
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	c.write("connected", True)
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	s()
	h.write_ALL("Test", "test of port 1")
	s()
	assert(c.get("Test") == "test of port 1")
	assert(c.get("Test2") is None)
	h.write_ALL("Test2", "test of port 2")
	s()
	assert(c.get("Test") == "test of port 1")
	assert(c.get("Test2") == "test of port 2")
	assert(h.get_ALL("Test") == [])
	assert(h.get_ALL("Test2") == [])
	h.close()
	c.close()
	success("Host -> Client Passed ({:.5f} sec)".format(time.time()-start))

def test_bidirectional_messages():
	start = time.time()
	h, c = initialize()
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	c.write("connected", True)
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	s()
	h.write_ALL("Test", "test of port 1")
	h.write_ALL("Test2", "test of port 2")
	c.write("Test", "test of port 1")
	s(0.1)
	c.write("Test2", "test of port 2")
	s()
	assert(c.get("Test") == "test of port 1")
	assert(c.get("Test2") == "test of port 2")
	assert(h.get_ALL("Test") == ["test of port 1"])
	assert(h.get_ALL("Test2") == ["test of port 2"])
	h.close()
	c.close()
	success("Host <-> Client Passed ({:.5f} sec)".format(time.time()-start))

def test_high_speed_host():
	start = time.time()
	h, c = initialize()
	c.write("connected", True)
	s()
	for i in range(10):
		h.write_ALL("Test{}".format(i), "test of port {}".format(i))
	s(0.1)
	for i in range(10):
		assert(c.get("Test{}".format(i)) == "test of port {}".format(i))
	c.close()
	h.close()
	success("High Speed Host -> Client Passed ({:.5f} sec)".format(time.time()-start))

def test_high_throughput_host():
	start = time.time()
	h, c = initialize()
	c.write("connected", True)
	s()
	for i in range(1000):
		h.write_ALL("Test{}".format(i), text)
	s()
	for i in range(1000):
		assert(c.get("Test{}".format(i)) == text)
	c.close()
	h.close()
	success("High Throughput Host -> Client Passed ({:.5f} sec)".format(time.time()-start))

def test_high_throughput_client():
	start = time.time()
	h, c = initialize()
	c.write("connected", True)
	s()
	for i in range(1000):
		c.write("Test{}".format(i), text)
	s()
	for i in range(1000):
		assert(h.get_ALL("Test{}".format(i)) == [text])
	c.close()
	h.close()
	success("High Throughput Client -> Host Passed ({:.5f} sec)".format(time.time()-start))

def test_high_throughput_bidirectional():
	start = time.time()
	h, c = initialize()
	c.write("connected", True)
	s()
	for i in range(1000):
		c.write("Test{}".format(i), text)
		h.write_ALL("Test{}".format(i), text)
	s()
	for i in range(1000):
		assert(h.get_ALL("Test{}".format(i)) == [text])
	for i in range(1000):
		assert(c.get("Test{}".format(i)) == text)
	c.close()
	h.close()
	success("High Throughput Host <-> Client Passed ({:.5f} sec)".format(time.time()-start))

def stress_test(stress=5, messages=1000):
	h = host(timeout=TIMEOUT)
	h.start()
	clients = []
	for i in range(stress):
		c = client(timeout=TIMEOUT).start()
		c.write("connected", True)
		clients.append(c)
	report("All sockets connected")
	s()
	for i in range(messages):
		for c in clients:
			c.write("Test{}".format(i), text)
		h.write_ALL("Test{}".format(i), text)
	report("All data written")
	s()
	for i in range(messages):
		assert(h.get_ALL("Test{}".format(i)) == [text]*stress)
	for i in range(messages):
		for c in clients:
			assert(c.get("Test{}".format(i)) == text)
	report("All data asserted")
	for c in clients:
		c.close()
	h.close()

def stress_test_v1():
	start = time.time()
	stress_test()
	success("Stress Test (v1) Passed ({:.5f} sec)".format(time.time()-start))

def stress_test_v2():
	start = time.time()
	stress_test(stress=10)
	success("Stress Test (v2) Passed ({:.5f} sec)".format(time.time()-start))

def stress_test_v3():
	start = time.time()
	stress_test(stress=20)
	success("Stress Test (v3) Passed ({:.5f} sec)".format(time.time()-start))

def stress_test_v4():
	start = time.time()
	stress_test(stress=10, messages=5000)
	success("Stress Test (v4) Passed ({:.5f} sec)".format(time.time()-start))

def multi_host_stress_test(stress=5, messages=1000, ports=[8080, 8081, 8082]):
	hosts = []
	for port in ports:
		hosts.append(host(timeout=TIMEOUT, port=port).start())
	clients = []
	for i in range(stress):
		for port in ports:
			c = client(timeout=TIMEOUT, port=port).start()
			c.write("connected", True)
			clients.append(c)
	report("All sockets connected")
	s()
	for i in range(messages):
		for c in clients:
			c.write("Test{}".format(i), text)
		for h in hosts:
			h.write_ALL("Test{}".format(i), text)
	report("All data written")
	s()
	for i in range(messages):
		for h in hosts:
			assert(h.get_ALL("Test{}".format(i)) == [text]*stress)
	for i in range(messages):
		for c in clients:
			assert(c.get("Test{}".format(i)) == text)
	report("All data asserted")
	for c in clients:
		c.close()
	for h in hosts:
		h.close()

def multi_host_stress_test_v1():
	start = time.time()
	multi_host_stress_test()
	success("Multi-Host Stress Test (v1) Passed ({:.5f} sec)".format(time.time()-start))

def multi_host_stress_test_v2():
	start = time.time()
	multi_host_stress_test(stress=10, ports=range(8080, 8085))
	success("Multi-Host Stress Test (v2) Passed ({:.5f} sec)".format(time.time()-start))

def multi_host_stress_test_v3():
	start = time.time()
	multi_host_stress_test(ports=range(8080, 8089))
	success("Multi-Host Stress Test (v3) Passed ({:.5f} sec)".format(time.time()-start))


###################
### TEST RUNNER ###
###################

def main(args):
	global DEBUG, DELAY
	if args.debug:
		DEBUG = True
	if args.sleep:
		DELAY = args.sleep
	routines = [test_connection_BOTH, test_async_ordering, test_empty_message, 
				test_host_messages, test_client_messages, test_bidirectional_messages,
				test_high_speed_host, test_high_throughput_host, test_high_throughput_client,
				test_high_throughput_bidirectional, stress_test_v1, stress_test_v2,
				stress_test_v3, stress_test_v4, multi_host_stress_test_v1,
				multi_host_stress_test_v2, multi_host_stress_test_v3]
	num = args.num or 1
	for i in range(num):
		for test in routines:
			test()
	print()
	success("All tests completed successfully")


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Automated testing for the socket.engine library')
	parser.add_argument('-n', '--num', help='The number of times each test should run', type=int)
	parser.add_argument('-d', '--debug', help='Turns on extra debugging messages', action='store_true')
	parser.add_argument('-s', '--sleep', help='Sleep timer between actions (default {})'.format(DELAY), type=float)
	args = parser.parse_args()
	main(args)
