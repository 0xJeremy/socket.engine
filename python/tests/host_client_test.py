#!/usr/bin/env python3

# pylint: disable=wrong-import-position, no-member, global-statement
import sys
import os

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

import time
import argparse
from socketengine import Client
from socketengine import Host

TIMEOUT = 0.5
DELAY = 0.5
DEBUG = False

########################
### HELPER FUNCTIONS ###
########################

# pylint: disable=invalid-name


def s(a=DELAY):
    time.sleep(a)


def report(message):
    global DEBUG
    if DEBUG:
        print("\033[93m[{}]\033[0m".format(message))


def success(message):
    print("\033[32m[{}]\033[0m".format(message))
    s(1)


def initialize():
    host = Host(timeout=TIMEOUT)
    client = Client(timeout=TIMEOUT)
    report("Sockets initialized")
    host.start()
    client.start()
    report("Sockets started")
    return host, client


# pylint: disable=line-too-long

text = "Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor matchost. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. "

##################
### UNIT TESTS ###
##################


def testConnectionBoth():
    start = time.time()
    host = Host(timeout=TIMEOUT)
    host.start()
    client = Client(timeout=TIMEOUT)
    client.start()
    report("Sockets opened and started")
    assert host.opened
    assert client.opened
    s(TIMEOUT)
    assert len(host.getClients()) == 1
    report("Open state verified")
    client.close()
    assert not client.opened and client.stopped
    host.close()
    report("Closed state verified")
    assert not host.opened and host.stopped
    success("Connection test Passed ({:.5f} sec)".format(time.time() - start))


def testAsyncOrdering():
    start = time.time()
    host = Host(timeout=TIMEOUT, open=False)
    client = Client(timeout=TIMEOUT, open=False)
    assert not host.opened
    host.open()
    host.start()
    assert host.opened
    report("Host started")
    client.open()
    client.start()
    assert client.opened
    report("Client started")
    host.close()
    assert host.stopped
    report("Host closed")
    client.close()
    assert client.stopped
    report("Client closed")
    success("Async Ordering test Passed ({:.5f} sec)".format(time.time() - start))


def testEmptyMessages():
    start = time.time()
    host, client = initialize()
    assert client.get("Test") is None
    assert client.get("Test2") is None
    assert host.getAll("Test") == []
    assert host.getAll("Test2") == []
    client.close()
    host.close()
    success("Empty messages test Passed ({:.5f} sec)".format(time.time() - start))


def testHostMessages():
    start = time.time()
    host, client = initialize()
    assert host.getAll("Test") == []
    assert host.getAll("Test2") == []
    client.write("Test", "test of port 1")
    s()
    assert host.getAll("Test") == ["test of port 1"]
    assert host.getAll("Test2") == []
    client.write("Test2", "test of port 2")
    s()
    assert host.getAll("Test") == ["test of port 1"]
    assert host.getAll("Test2") == ["test of port 2"]
    assert client.get("Test") is None
    assert client.get("Test2") is None
    client.close()
    host.close()
    success("Client -> Host Passed ({:.5f} sec)".format(time.time() - start))


def testClientMessages():
    start = time.time()
    host, client = initialize()
    assert client.get("Test") is None
    assert client.get("Test2") is None
    client.write("connected", True)
    assert client.get("Test") is None
    assert client.get("Test2") is None
    s()
    host.writeAll("Test", "test of port 1")
    s()
    assert client.get("Test") == "test of port 1"
    assert client.get("Test2") is None
    host.writeAll("Test2", "test of port 2")
    s()
    assert client.get("Test") == "test of port 1"
    assert client.get("Test2") == "test of port 2"
    assert host.getAll("Test") == []
    assert host.getAll("Test2") == []
    host.close()
    client.close()
    success("Host -> Client Passed ({:.5f} sec)".format(time.time() - start))


def testBidirectionalMessages():
    start = time.time()
    host, client = initialize()
    assert client.get("Test") is None
    assert client.get("Test2") is None
    client.write("connected", True)
    assert client.get("Test") is None
    assert client.get("Test2") is None
    s()
    host.writeAll("Test", "test of port 1")
    host.writeAll("Test2", "test of port 2")
    client.write("Test", "test of port 1")
    s(0.1)
    client.write("Test2", "test of port 2")
    s()
    assert client.get("Test") == "test of port 1"
    assert client.get("Test2") == "test of port 2"
    assert host.getAll("Test") == ["test of port 1"]
    assert host.getAll("Test2") == ["test of port 2"]
    host.close()
    client.close()
    success("Host <-> Client Passed ({:.5f} sec)".format(time.time() - start))


def testHighSpeedHost():
    start = time.time()
    host, client = initialize()
    client.write("connected", True)
    s()
    for i in range(10):
        host.writeAll("Test{}".format(i), "test of port {}".format(i))
    s(0.1)
    for i in range(10):
        assert client.get("Test{}".format(i)) == "test of port {}".format(i)
    client.close()
    host.close()
    success("High Speed Host -> Client Passed ({:.5f} sec)".format(time.time() - start))


def testHighThroughputHost():
    start = time.time()
    host, client = initialize()
    client.write("connected", True)
    s()
    for i in range(1000):
        host.writeAll("Test{}".format(i), text)
    s()
    for i in range(1000):
        assert client.get("Test{}".format(i)) == text
    client.close()
    host.close()
    success("High Throughput Host -> Client Passed ({:.5f} sec)".format(time.time() - start))


def testHighThroughputClient():
    start = time.time()
    host, client = initialize()
    client.write("connected", True)
    s()
    for i in range(1000):
        client.write("Test{}".format(i), text)
    s()
    for i in range(1000):
        assert host.getAll("Test{}".format(i)) == [text]
    client.close()
    host.close()
    success("High Throughput Client -> Host Passed ({:.5f} sec)".format(time.time() - start))


def testHighThroughputBidirectional():
    start = time.time()
    host, client = initialize()
    client.write("connected", True)
    s()
    for i in range(1000):
        client.write("Test{}".format(i), text)
        host.writeAll("Test{}".format(i), text)
    s()
    for i in range(1000):
        assert host.getAll("Test{}".format(i)) == [text]
    for i in range(1000):
        assert client.get("Test{}".format(i)) == text
    client.close()
    host.close()
    success("High Throughput Host <-> Client Passed ({:.5f} sec)".format(time.time() - start))


def stressTest(stress=5, messages=1000):
    host = Host(timeout=TIMEOUT)
    host.start()
    clients = []
    for i in range(stress):
        client = Client(timeout=TIMEOUT).start()
        client.write("connected", True)
        clients.append(client)
    report("All sockets connected")
    s()
    for i in range(messages):
        for client in clients:
            client.write("Test{}".format(i), text)
        host.writeAll("Test{}".format(i), text)
    report("All data written")
    s()
    for i in range(messages):
        assert host.getAll("Test{}".format(i)) == [text] * stress
    for i in range(messages):
        for client in clients:
            assert client.get("Test{}".format(i)) == text
    report("All data asserted")
    for client in clients:
        client.close()
    host.close()


def stressTestV1():
    start = time.time()
    stressTest()
    success("Stress Test (v1) Passed ({:.5f} sec)".format(time.time() - start))


def stressTestV2():
    start = time.time()
    stressTest(stress=10)
    success("Stress Test (v2) Passed ({:.5f} sec)".format(time.time() - start))


def stressTestV3():
    start = time.time()
    stressTest(stress=20)
    success("Stress Test (v3) Passed ({:.5f} sec)".format(time.time() - start))


def stressTestV4():
    start = time.time()
    stressTest(stress=10, messages=5000)
    success("Stress Test (v4) Passed ({:.5f} sec)".format(time.time() - start))


# pylint: disable=dangerous-default-value
def multiHostStressTest(stress=5, messages=1000, ports=[8080, 8081, 8082]):
    hosts = []
    for port in ports:
        hosts.append(Host(timeout=TIMEOUT, port=port).start())
    clients = []
    for i in range(stress):
        for port in ports:
            client = Client(timeout=TIMEOUT, port=port).start()
            client.write("connected", True)
            clients.append(client)
    report("All sockets connected")
    s()
    for i in range(messages):
        for client in clients:
            client.write("Test{}".format(i), text)
        for host in hosts:
            host.writeAll("Test{}".format(i), text)
    report("All data written")
    s()
    for i in range(messages):
        for host in hosts:
            assert host.getAll("Test{}".format(i)) == [text] * stress
    for i in range(messages):
        for client in clients:
            assert client.get("Test{}".format(i)) == text
    report("All data asserted")
    for client in clients:
        client.close()
    for host in hosts:
        host.close()


def multiHostStressTestV1():
    start = time.time()
    multiHostStressTest()
    success("Multi-Host Stress Test (v1) Passed ({:.5f} sec)".format(time.time() - start))


def multiHostStressTestV2():
    start = time.time()
    multiHostStressTest(stress=10, ports=range(8080, 8085))
    success("Multi-Host Stress Test (v2) Passed ({:.5f} sec)".format(time.time() - start))


def multiHostStressTestV3():
    start = time.time()
    multiHostStressTest(ports=range(8080, 8089))
    success("Multi-Host Stress Test (v3) Passed ({:.5f} sec)".format(time.time() - start))


###################
### TEST RUNNER ###
###################


def main(args):
    global DEBUG, DELAY
    if args.debug:
        DEBUG = True
    if args.sleep:
        DELAY = args.sleep
    routines = [
        testConnectionBoth,
        testAsyncOrdering,
        testEmptyMessages,
        testHostMessages,
        testClientMessages,
        testBidirectionalMessages,
        testHighSpeedHost,
        testHighThroughputHost,
        testHighThroughputClient,
        testHighThroughputBidirectional,
        stressTestV1,
        stressTestV2,
        stressTestV3,
        stressTestV4,
        multiHostStressTestV1,
        multiHostStressTestV2,
        multiHostStressTestV3,
    ]
    num = args.num or 1
    # pylint: disable=unused-variable
    for i in range(num):
        for test in routines:
            test()
    print()
    success("All tests completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated testing for the socket.engine library")
    parser.add_argument("-n", "--num", help="The number of times each test should run", type=int)
    parser.add_argument(
        "-d", "--debug", help="Turns on extra debugging messages", action="store_true",
    )
    parser.add_argument(
        "-s", "--sleep", help="Sleep timer between actions (default {})".format(DELAY), type=float,
    )
    arguments = parser.parse_args()
    main(arguments)
