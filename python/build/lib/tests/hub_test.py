#!/usr/bin/env python3

import sys
import os

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from socketengine import Hub
from socketengine import Transport
import time
import argparse

TIMEOUT = 0.5
DELAY = 0.5
DEBUG = False
CHANNEL = "Test"

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
    h1 = Hub(timeout=TIMEOUT)
    h2 = Hub(timeout=TIMEOUT)
    h1.connect(CHANNEL, "127.0.0.1", h2.port)
    report("Hubs created and started")
    s(0.1)
    return h1, h2


text = "Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor match. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. "

##################
### UNIT TESTS ###
##################


def test_hub_transport_setup():
    start = time.time()
    h1 = Hub(timeout=TIMEOUT)
    h2 = Hub(timeout=TIMEOUT)
    report("Hubs created and started")
    assert h1.opened
    assert not h1.stopped
    assert h2.opened
    assert not h2.stopped
    h1.connect(CHANNEL, "127.0.0.1", h2.port)
    s(0.1)
    assert len(h1.transports) is 1
    assert len(h2.transports) is 1
    h1.close()
    h2.close()
    assert not h1.opened
    assert h1.stopped
    assert not h2.opened
    assert h1.stopped
    success("Hub Connection Setup Test Passed ({:.5f} sec)".format(time.time() - start))


def test_transport_setup():
    start = time.time()
    h1 = Hub(timeout=TIMEOUT)
    h2 = Hub(timeout=TIMEOUT)
    report("Hubs created and started")
    h1.connect(CHANNEL, "127.0.0.1", h2.port)
    s(0.1)
    assert len(h1.transports) is 1
    assert len(h2.transports) is 1
    c1 = h1.transports[0]
    c2 = h2.transports[0]
    assert c1.opened
    assert not c1.stopped
    assert c2.opened
    assert not c2.stopped
    assert c1.name == CHANNEL
    assert c2.name == CHANNEL
    assert c1.addr == "127.0.0.1"
    assert c2.addr == "127.0.0.1"
    h1.close()
    h2.close()
    s(TIMEOUT)
    assert not c1.opened
    assert c1.stopped
    assert not c2.opened
    assert c2.stopped
    success("Connection Setup Test Passed ({:.5f} sec)".format(time.time() - start))


def test_empty_messages():
    start = time.time()
    h1 = Hub(timeout=TIMEOUT)
    h2 = Hub(timeout=TIMEOUT)
    assert h1.get_all("Test") == []
    assert h2.get_all("Test") == []
    assert h1.get_all("Test2") == []
    assert h2.get_all("Test2") == []
    h1.connect("Test", "127.0.0.1", h2.port)
    s(0.1)
    assert h1.get_all("Test") == []
    assert h2.get_all("Test") == []
    assert h1.get_all("Test2") == []
    assert h2.get_all("Test2") == []
    h1.close()
    h2.close()
    success("Empty messages Test Passed ({:.5f} sec)".format(time.time() - start))


def test_oneway_messages():
    start = time.time()
    h1 = Hub(timeout=TIMEOUT)
    h2 = Hub(timeout=TIMEOUT)
    assert h1.get_all("Test") == []
    assert h2.get_all("Test") == []
    assert h1.get_all("Test2") == []
    assert h2.get_all("Test2") == []
    h1.connect("Test", "127.0.0.1", h2.port)
    s(0.1)
    h1.write_to_name("Test", "Test", "test of port 1")
    s(0.05)
    assert h1.get_all("Test") == []
    assert h2.get_all("Test") == ["test of port 1"]
    assert h1.get_all("Test2") == []
    assert h2.get_all("Test2") == []
    h1.write_to_name("Test", "Test2", "test of port 2")
    s(0.05)
    assert h1.get_all("Test") == []
    assert h2.get_all("Test") == ["test of port 1"]
    assert h1.get_all("Test2") == []
    assert h2.get_all("Test2") == ["test of port 2"]
    h1.close()
    h2.close()
    success("One-way messages Test Passed ({:.5f} sec)".format(time.time() - start))


def test_bidirectional_messages():
    start = time.time()
    h1, h2 = initialize()
    assert h1.get_all("Test") == []
    assert h2.get_all("Test") == []
    assert h1.get_all("Test2") == []
    assert h2.get_all("Test2") == []
    h1.write_to_name("Test", "Test", "test of port 1")
    h2.write_to_name("Test", "Test", "test of port 1")
    s(0.05)
    assert h1.get_all("Test") == ["test of port 1"]
    assert h2.get_all("Test") == ["test of port 1"]
    assert h1.get_all("Test2") == []
    assert h2.get_all("Test2") == []
    h1.write_to_name("Test", "Test2", "test of port 2")
    h2.write_to_name("Test", "Test2", "test of port 2")
    s(0.05)
    assert h1.get_all("Test") == ["test of port 1"]
    assert h2.get_all("Test") == ["test of port 1"]
    assert h1.get_all("Test2") == ["test of port 2"]
    assert h2.get_all("Test2") == ["test of port 2"]
    h1.close()
    h2.close()
    success(
        "Bidirectional messages Test Passed ({:.5f} sec)".format(time.time() - start)
    )


def test_high_speed(num=10, bidirectional=False, sleep=0.1):
    h1, h2 = initialize()
    for i in range(num):
        h1.write_to_name(CHANNEL, "test{}".format(i), text)
        if bidirectional:
            h2.write_to_name(CHANNEL, "test{}".format(i), text)
    s(sleep)
    assert len(h1.transports) == len(h2.transports)
    for i in range(num):
        if bidirectional:
            assert h1.get_all("test{}".format(i)) == [text]
        assert h2.get_all("test{}".format(i)) == [text]
    h1.close()
    h2.close()


def test_oneway_high_speed():
    start = time.time()
    test_high_speed()
    success("One-way High Speed Test Passed ({:.5f} sec)".format(time.time() - start))


def test_bidirectional_high_speed():
    start = time.time()
    test_high_speed(bidirectional=True)
    success(
        "Bidirectional High Speed Test Passed ({:.5f} sec)".format(time.time() - start)
    )


def test_oneway_high_throughput():
    start = time.time()
    test_high_speed(num=1000)
    success(
        "One-way High Throughput Test Passed ({:.5f} sec)".format(time.time() - start)
    )


def test_bidirectional_high_throughput():
    start = time.time()
    test_high_speed(num=1000, bidirectional=True, sleep=2)
    success(
        "Bidirectional High Throughput Test Passed ({:.5f} sec)".format(
            time.time() - start
        )
    )


def test_extreme_throughput():
    start = time.time()
    test_high_speed(num=10000, bidirectional=True, sleep=2)
    success("Extreme Throughput Test Passed ({:.5f} sec)".format(time.time() - start))


def multi_transports(num_conn=10, messages=10, bidirectional=False):
    h1 = Hub(timeout=TIMEOUT)
    h2 = Hub(timeout=TIMEOUT)
    for i in range(num_conn):
        h1.connect("Test{}".format(i), "127.0.0.1", h2.port)
    s()
    assert len(h1.transports) == len(h2.transports)
    for i in range(messages):
        h1.write_all("Test{}".format(i), text)
        if bidirectional:
            h2.write_all("Test{}".format(i), text)
    s()
    for i in range(messages):
        if bidirectional:
            assert h1.get_all("Test{}".format(i)) == [text] * num_conn
        assert h2.get_all("Test{}".format(i)) == [text] * num_conn
    h1.close()
    h2.close()


def test_multi_transports_oneway():
    start = time.time()
    multi_transports()
    success(
        "Multi-Connection One-Way Test Passed ({:.5f} sec)".format(time.time() - start)
    )


def test_multi_transports_bidirectional():
    start = time.time()
    multi_transports(bidirectional=True)
    success(
        "Multi-Connection Bidirectional Test Passed ({:.5f} sec)".format(
            time.time() - start
        )
    )


def test_multiple_transports_stress():
    start = time.time()
    multi_transports(num_conn=25, messages=1000, bidirectional=True)
    success(
        "Multi-Connection Stress Test Passed ({:.5f} sec)".format(time.time() - start)
    )


def stress_test(stress=5, messages=1000):
    h1 = Hub(timeout=TIMEOUT)
    h2 = Hub(timeout=TIMEOUT)
    for i in range(stress):
        if i % 2 == 0:
            h1.connect("Test{}".format(i), "127.0.0.1", h2.port)
        else:
            h2.connect("Test{}".format(i), "127.0.0.1", h1.port)
    s()
    assert len(h1.transports) == len(h2.transports)
    for i in range(messages):
        h1.write_all("Test{}".format(i), text)
        h2.write_all("Test{}".format(i), text)
    s()
    for i in range(messages):
        assert h1.get_all("Test{}".format(i)) == [text] * stress
        assert h2.get_all("Test{}".format(i)) == [text] * stress
    h1.close()
    h2.close()


def stress_test_v1():
    start = time.time()
    stress_test()
    success("Stress Test (v1) Passed ({:.5f} sec)".format(time.time() - start))


def stress_test_v2():
    start = time.time()
    stress_test(stress=10)
    success("Stress Test (v2) Passed ({:.5f} sec)".format(time.time() - start))


def stress_test_v3():
    start = time.time()
    stress_test(stress=25)
    success("Stress Test (v3) Passed ({:.5f} sec)".format(time.time() - start))


def stress_test_v4():
    start = time.time()
    stress_test(stress=25, messages=5000)
    success("Stress Test (v4) Passed ({:.5f} sec)".format(time.time() - start))


def multi_hub_stress_test(stress=5, messages=1000):
    hubs = []
    for i in range(stress):
        h = Hub(timeout=TIMEOUT)
        hubs.append(h)
    report("Hubs created")
    for h1 in hubs:
        for h2 in hubs:
            h2.connect("Test", "127.0.0.1", h1.port)
    report("Hubs linked")
    s()
    for h in hubs:
        assert len(h.transports) == 2 * stress
    report("Hub transports verified")
    for h in hubs:
        for i in range(messages):
            h.write_all("Test{}".format(i), text)
    report("Writing finished")
    s()
    for h in hubs:
        for i in range(messages):
            assert h.get_all("Test{}".format(i)) == [text] * 2 * stress
    report("Hub messages verified")
    for h in hubs:
        h.close()


def multi_host_stress_test_v1():
    start = time.time()
    multi_hub_stress_test()
    success(
        "Multi-Host Stress Test (v1) Passed ({:.5f} sec)".format(time.time() - start)
    )


def multi_host_stress_test_v2():
    start = time.time()
    multi_hub_stress_test(stress=10)
    success(
        "Multi-Host Stress Test (v2) Passed ({:.5f} sec)".format(time.time() - start)
    )


def multi_host_stress_test_v3():
    start = time.time()
    multi_hub_stress_test(stress=10, messages=5000)
    success(
        "Multi-Host Stress Test (v3) Passed ({:.5f} sec)".format(time.time() - start)
    )


# This test read/wrote 4.412gb of data in 818.95143 seconds.
# It isn't worth running usually.
# def multi_host_stress_test_v4():
# 	start = time.time()
# 	multi_hub_stress_test(stress=20, messages=5000)
# 	success("Multi-Host Stress Test (v4) Passed ({:.5f} sec)".format(time.time()-start))


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
        test_hub_transport_setup,
        test_transport_setup,
        test_empty_messages,
        test_oneway_messages,
        test_bidirectional_messages,
        test_oneway_high_speed,
        test_bidirectional_high_speed,
        test_oneway_high_throughput,
        test_bidirectional_high_throughput,
        test_extreme_throughput,
        test_multi_transports_oneway,
        test_multi_transports_bidirectional,
        test_multiple_transports_stress,
        stress_test_v1,
        stress_test_v2,
        stress_test_v3,
        stress_test_v4,
        multi_host_stress_test_v1,
        multi_host_stress_test_v2,
        multi_host_stress_test_v3,
    ]
    num = args.num or 1
    for i in range(num):
        for test in routines:
            test()
    print()
    success("All tests completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automated testing for the socket.engine library"
    )
    parser.add_argument(
        "-n", "--num", help="The number of times each test should run", type=int
    )
    parser.add_argument(
        "-d", "--debug", help="Turns on extra debugging messages", action="store_true"
    )
    parser.add_argument(
        "-s",
        "--sleep",
        help="Sleep timer between actions (default {})".format(DELAY),
        type=float,
    )
    args = parser.parse_args()
    main(args)
