from client import client
from host import host
import time
from threading import Thread

TIMEOUT = 0.5
DELAY = 5
DEBUG = False

def s(a=DELAY):
	time.sleep(a)

def report(text):
	if DEBUG:
		print("\033[93m[{}]\033[0m".format(text))

def success(text):
	print("\033[32m[{}]\033[0m".format(text))
	s(1)


text = "Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor match. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. "


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

def test_empty_message():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	h.start()
	c.start()
	report("Sockets started")
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	assert(h.get_ALL("Test") == [])
	assert(h.get_ALL("Test2") == [])
	c.close()
	h.close()
	success("Empty messages test passed")

test_empty_message()

def test_host_messages():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	h.start()
	c.start()
	report("Sockets started")
	assert(h.get_ALL("Test") == [])
	assert(h.get_ALL("Test2") == [])
	c.write("Test", "test of port 1")
	s(0.5)
	assert(h.get_ALL("Test") == ["test of port 1"])
	assert(h.get_ALL("Test2") == [])
	c.write("Test2", "test of port 2")
	s(0.5)
	assert(h.get_ALL("Test") == ["test of port 1"])
	assert(h.get_ALL("Test2") == ["test of port 2"])
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	c.close()
	h.close()
	success("Client -> Host Passed")

test_host_messages()

def test_client_messages():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	h.start()
	c.start()
	report("Sockets started")
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	c.write("connected", True)
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	s(0.5)
	h.write_ALL("Test", "test of port 1")
	s(0.5)
	assert(c.get("Test") == "test of port 1")
	assert(c.get("Test2") is None)
	h.write_ALL("Test2", "test of port 2")
	s(0.5)
	assert(c.get("Test") == "test of port 1")
	assert(c.get("Test2") == "test of port 2")
	assert(h.get_ALL("Test") == [])
	assert(h.get_ALL("Test2") == [])
	h.close()
	c.close()
	success("Host -> Client Passed")

test_client_messages()

def test_bidirectional_messages():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	h.start()
	c.start()
	report("Sockets started")
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	c.write("connected", True)
	assert(c.get("Test") is None)
	assert(c.get("Test2") is None)
	s(0.5)
	h.write_ALL("Test", "test of port 1")
	h.write_ALL("Test2", "test of port 2")
	c.write("Test", "test of port 1")
	s(0.1)
	c.write("Test2", "test of port 2")
	s(0.5)
	assert(c.get("Test") == "test of port 1")
	assert(c.get("Test2") == "test of port 2")
	assert(h.get_ALL("Test") == ["test of port 1"])
	assert(h.get_ALL("Test2") == ["test of port 2"])
	h.close()
	c.close()
	success("Host <-> Client Passed")

test_bidirectional_messages()

def test_high_speed_host():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	h.start()
	c.start()
	report("Sockets started")
	c.write("connected", True)
	s(0.5)
	h.write_ALL("Test0", "test of port 0")
	h.write_ALL("Test1", "test of port 1")
	h.write_ALL("Test2", "test of port 2")
	h.write_ALL("Test3", "test of port 3")
	h.write_ALL("Test4", "test of port 4")
	h.write_ALL("Test5", "test of port 5")
	h.write_ALL("Test6", "test of port 6")
	h.write_ALL("Test7", "test of port 7")
	h.write_ALL("Test8", "test of port 8")
	h.write_ALL("Test9", "test of port 9")
	s(0.1)
	assert(c.get("Test0") == "test of port 0")
	assert(c.get("Test1") == "test of port 1")
	assert(c.get("Test2") == "test of port 2")
	assert(c.get("Test3") == "test of port 3")
	assert(c.get("Test4") == "test of port 4")
	assert(c.get("Test5") == "test of port 5")
	assert(c.get("Test6") == "test of port 6")
	assert(c.get("Test7") == "test of port 7")
	assert(c.get("Test8") == "test of port 8")
	assert(c.get("Test9") == "test of port 9")
	c.close()
	h.close()
	success("High Speed Host -> Client Passed")

test_high_speed_host()

def test_high_throughput_host():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	h.start()
	c.start()
	report("Sockets started")
	c.write("connected", True)
	s(0.5)
	for i in range(1000):
		h.write_ALL("Test{}".format(i), text)
	s(0.5)
	for i in range(1000):
		assert(c.get("Test{}".format(i)) == text)
	c.close()
	h.close()
	success("High Throughput Host -> Client Passed")

test_high_throughput_host()

def test_high_throughput_client():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	h.start()
	c.start()
	report("Sockets started")
	c.write("connected", True)
	s(0.5)
	for i in range(1000):
		c.write("Test{}".format(i), text)
	s(0.5)
	for i in range(1000):
		assert(h.get_ALL("Test{}".format(i)) == [text])
	c.close()
	h.close()
	success("High Throughput Client -> Host Passed")

test_high_throughput_client()

def test_high_throughput_bidirectional():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	h.start()
	c.start()
	report("Sockets started")
	c.write("connected", True)
	s(0.5)
	for i in range(1000):
		c.write("Test{}".format(i), text)
		h.write_ALL("Test{}".format(i), text)
	s(0.5)
	for i in range(1000):
		assert(h.get_ALL("Test{}".format(i)) == [text])
	for i in range(1000):
		assert(c.get("Test{}".format(i)) == text)
	c.close()
	h.close()
	success("High Throughput Host <-> Client Passed")

test_high_throughput_bidirectional()