#!/usr/bin/env python3

# pylint: disable=wrong-import-position, no-member, global-statement
import sys
import os

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

import time
import argparse
from socketengine import Hub

TIMEOUT = 0.5
DELAY = 0.5
DEBUG = False
CHANNEL = 'Test'

########################
### HELPER FUNCTIONS ###
########################

# pylint: disable=invalid-name


def s(a=DELAY):
    time.sleep(a)


def report(message):
    global DEBUG
    if DEBUG:
        print('\033[93m[{}]\033[0m'.format(message))


def success(message):
    print('\033[32m[{}]\033[0m'.format(message))
    s(1)


def initialize():
    hubOne = Hub(timeout=TIMEOUT)
    hubTwo = Hub(timeout=TIMEOUT)
    hubOne.connect(CHANNEL, '127.0.0.1', hubTwo.port)
    report('Hubs created and started')
    s(0.1)
    return hubOne, hubTwo


# pylint: disable=line-too-long

text = 'Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor matchub. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. '

##################
### UNIT TESTS ###
##################


def testHubTransportSetup():
    start = time.time()
    hubOne = Hub(timeout=TIMEOUT)
    hubTwo = Hub(timeout=TIMEOUT)
    report('Hubs created and started')
    assert hubOne.opened
    assert not hubOne.stopped
    assert hubTwo.opened
    assert not hubTwo.stopped
    hubOne.connect(CHANNEL, '127.0.0.1', hubTwo.port)
    s(0.1)
    assert len(hubOne.transports) == 1
    assert len(hubTwo.transports) == 1
    hubOne.close()
    hubTwo.close()
    assert not hubOne.opened
    assert hubOne.stopped
    assert not hubTwo.opened
    assert hubOne.stopped
    success('Hub Connection Setup Test Passed ({:.5f} sec)'.format(time.time() - start))


def testTransportSetup():
    start = time.time()
    hubOne = Hub(timeout=TIMEOUT)
    hubTwo = Hub(timeout=TIMEOUT)
    report('Hubs created and started')
    hubOne.connect(CHANNEL, '127.0.0.1', hubTwo.port)
    s(0.1)
    assert len(hubOne.transports) == 1
    assert len(hubTwo.transports) == 1
    transportOne = hubOne.transports[0]
    transportTwo = hubTwo.transports[0]
    assert transportOne.opened
    assert not transportOne.stopped
    assert transportTwo.opened
    assert not transportTwo.stopped
    assert transportOne.name == CHANNEL
    assert transportTwo.name == CHANNEL
    assert transportOne.addr == '127.0.0.1'
    assert transportTwo.addr == '127.0.0.1'
    hubOne.close()
    hubTwo.close()
    s(TIMEOUT)
    assert not transportOne.opened
    assert transportOne.stopped
    assert not transportTwo.opened
    assert transportTwo.stopped
    success('Connection Setup Test Passed ({:.5f} sec)'.format(time.time() - start))


def testEmptyMessages():
    start = time.time()
    hubOne = Hub(timeout=TIMEOUT)
    hubTwo = Hub(timeout=TIMEOUT)
    assert hubOne.getAll('Test') == []
    assert hubTwo.getAll('Test') == []
    assert hubOne.getAll('Test2') == []
    assert hubTwo.getAll('Test2') == []
    hubOne.connect('Test', '127.0.0.1', hubTwo.port)
    s(0.1)
    assert hubOne.getAll('Test') == []
    assert hubTwo.getAll('Test') == []
    assert hubOne.getAll('Test2') == []
    assert hubTwo.getAll('Test2') == []
    hubOne.close()
    hubTwo.close()
    success('Empty messages Test Passed ({:.5f} sec)'.format(time.time() - start))


def testOnewayMessages():
    start = time.time()
    hubOne = Hub(timeout=TIMEOUT)
    hubTwo = Hub(timeout=TIMEOUT)
    assert hubOne.getAll('Test') == []
    assert hubTwo.getAll('Test') == []
    assert hubOne.getAll('Test2') == []
    assert hubTwo.getAll('Test2') == []
    hubOne.connect('Test', '127.0.0.1', hubTwo.port)
    s(0.1)
    hubOne.writeToName('Test', 'Test', 'test of port 1')
    s(0.05)
    assert hubOne.getAll('Test') == []
    assert hubTwo.getAll('Test') == ['test of port 1']
    assert hubOne.getAll('Test2') == []
    assert hubTwo.getAll('Test2') == []
    hubOne.writeToName('Test', 'Test2', 'test of port 2')
    s(0.05)
    assert hubOne.getAll('Test') == []
    assert hubTwo.getAll('Test') == ['test of port 1']
    assert hubOne.getAll('Test2') == []
    assert hubTwo.getAll('Test2') == ['test of port 2']
    hubOne.close()
    hubTwo.close()
    success('One-way messages Test Passed ({:.5f} sec)'.format(time.time() - start))


def testBidirectionalMessages():
    start = time.time()
    hubOne, hubTwo = initialize()
    assert hubOne.getAll('Test') == []
    assert hubTwo.getAll('Test') == []
    assert hubOne.getAll('Test2') == []
    assert hubTwo.getAll('Test2') == []
    hubOne.writeToName('Test', 'Test', 'test of port 1')
    hubTwo.writeToName('Test', 'Test', 'test of port 1')
    s(0.05)
    assert hubOne.getAll('Test') == ['test of port 1']
    assert hubTwo.getAll('Test') == ['test of port 1']
    assert hubOne.getAll('Test2') == []
    assert hubTwo.getAll('Test2') == []
    hubOne.writeToName('Test', 'Test2', 'test of port 2')
    hubTwo.writeToName('Test', 'Test2', 'test of port 2')
    s(0.05)
    assert hubOne.getAll('Test') == ['test of port 1']
    assert hubTwo.getAll('Test') == ['test of port 1']
    assert hubOne.getAll('Test2') == ['test of port 2']
    assert hubTwo.getAll('Test2') == ['test of port 2']
    hubOne.close()
    hubTwo.close()
    success('Bidirectional messages Test Passed ({:.5f} sec)'.format(time.time() - start))


def testHighSpeed(num=10, bidirectional=False, sleep=0.1):
    hubOne, hubTwo = initialize()
    for i in range(num):
        hubOne.writeToName(CHANNEL, 'test{}'.format(i), text)
        if bidirectional:
            hubTwo.writeToName(CHANNEL, 'test{}'.format(i), text)
    s(sleep)
    assert len(hubOne.transports) == len(hubTwo.transports)
    for i in range(num):
        if bidirectional:
            assert hubOne.getAll('test{}'.format(i)) == [text]
        assert hubTwo.getAll('test{}'.format(i)) == [text]
    hubOne.close()
    hubTwo.close()


def testOnewayHighspeed():
    start = time.time()
    testHighSpeed()
    success('One-way High Speed Test Passed ({:.5f} sec)'.format(time.time() - start))


def testBidirectionalHighspeed():
    start = time.time()
    testHighSpeed(bidirectional=True)
    success('Bidirectional High Speed Test Passed ({:.5f} sec)'.format(time.time() - start))


def testOnewayHighThroughput():
    start = time.time()
    testHighSpeed(num=1000)
    success('One-way High Throughput Test Passed ({:.5f} sec)'.format(time.time() - start))


def testBidirectionalHighThroughput():
    start = time.time()
    testHighSpeed(num=1000, bidirectional=True, sleep=2)
    success('Bidirectional High Throughput Test Passed ({:.5f} sec)'.format(time.time() - start))


def testExtremeThroughput():
    start = time.time()
    testHighSpeed(num=10000, bidirectional=True, sleep=2)
    success('Extreme Throughput Test Passed ({:.5f} sec)'.format(time.time() - start))


def multiTransports(numConn=10, messages=10, bidirectional=False):
    hubOne = Hub(timeout=TIMEOUT)
    hubTwo = Hub(timeout=TIMEOUT)
    for i in range(numConn):
        hubOne.connect('Test{}'.format(i), '127.0.0.1', hubTwo.port)
    s()
    assert len(hubOne.transports) == len(hubTwo.transports)
    for i in range(messages):
        hubOne.writeAll('Test{}'.format(i), text)
        if bidirectional:
            hubTwo.writeAll('Test{}'.format(i), text)
    s()
    for i in range(messages):
        if bidirectional:
            assert hubOne.getAll('Test{}'.format(i)) == [text] * numConn
        assert hubTwo.getAll('Test{}'.format(i)) == [text] * numConn
    hubOne.close()
    hubTwo.close()


def testMultitransportsOneway():
    start = time.time()
    multiTransports()
    success('Multi-Connection One-Way Test Passed ({:.5f} sec)'.format(time.time() - start))


def testMultitransportsBidirectional():
    start = time.time()
    multiTransports(bidirectional=True)
    success('Multi-Connection Bidirectional Test Passed ({:.5f} sec)'.format(time.time() - start))


def testMultipleTransportsStressTest():
    start = time.time()
    multiTransports(numConn=25, messages=1000, bidirectional=True)
    success('Multi-Connection Stress Test Passed ({:.5f} sec)'.format(time.time() - start))


def stressTest(stress=5, messages=1000):
    hubOne = Hub(timeout=TIMEOUT)
    hubTwo = Hub(timeout=TIMEOUT)
    for i in range(stress):
        if i % 2 == 0:
            hubOne.connect('Test{}'.format(i), '127.0.0.1', hubTwo.port)
        else:
            hubTwo.connect('Test{}'.format(i), '127.0.0.1', hubOne.port)
    s()
    assert len(hubOne.transports) == len(hubTwo.transports)
    for i in range(messages):
        hubOne.writeAll('Test{}'.format(i), text)
        hubTwo.writeAll('Test{}'.format(i), text)
    s()
    for i in range(messages):
        assert hubOne.getAll('Test{}'.format(i)) == [text] * stress
        assert hubTwo.getAll('Test{}'.format(i)) == [text] * stress
    hubOne.close()
    hubTwo.close()


def stressTestV1():
    start = time.time()
    stressTest()
    success('Stress Test (v1) Passed ({:.5f} sec)'.format(time.time() - start))


def stressTestV2():
    start = time.time()
    stressTest(stress=10)
    success('Stress Test (v2) Passed ({:.5f} sec)'.format(time.time() - start))


def stressTestV3():
    start = time.time()
    stressTest(stress=25)
    success('Stress Test (v3) Passed ({:.5f} sec)'.format(time.time() - start))


def stressTestV4():
    start = time.time()
    stressTest(stress=25, messages=5000)
    success('Stress Test (v4) Passed ({:.5f} sec)'.format(time.time() - start))


def multiHubStresstest(stress=5, messages=1000):
    hubs = []
    for i in range(stress):
        hub = Hub(timeout=TIMEOUT)
        hubs.append(hub)
    report('Hubs created')
    for hubOne in hubs:
        for hubTwo in hubs:
            hubTwo.connect('Test', '127.0.0.1', hubOne.port)
    report('Hubs linked')
    s()
    for hub in hubs:
        assert len(hub.transports) == 2 * stress
    report('Hub transports verified')
    for hub in hubs:
        for i in range(messages):
            hub.writeAll('Test{}'.format(i), text)
    report('Writing finished')
    s()
    for hub in hubs:
        for i in range(messages):
            assert hub.getAll('Test{}'.format(i)) == [text] * 2 * stress
    report('Hub messages verified')
    for hub in hubs:
        hub.close()


def multihostStresstestV1():
    start = time.time()
    multiHubStresstest()
    success('Multi-Host Stress Test (v1) Passed ({:.5f} sec)'.format(time.time() - start))


def multihostStresstestV2():
    start = time.time()
    multiHubStresstest(stress=10)
    success('Multi-Host Stress Test (v2) Passed ({:.5f} sec)'.format(time.time() - start))


def multihostStresstestV3():
    start = time.time()
    multiHubStresstest(stress=10, messages=5000)
    success('Multi-Host Stress Test (v3) Passed ({:.5f} sec)'.format(time.time() - start))


# This test read/wrote 4.412gb of data in 818.95143 seconds.
# It isn't worth running usually.
# def multi_host_stressTestV4():
# 	start = time.time()
# 	multiHubStresstest(stress=20, messages=5000)
# 	success('Multi-Host Stress Test (v4) Passed ({:.5f} sec)'.format(time.time()-start))


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
        testHubTransportSetup,
        testTransportSetup,
        testEmptyMessages,
        testOnewayMessages,
        testBidirectionalMessages,
        testOnewayHighspeed,
        testBidirectionalHighspeed,
        testOnewayHighThroughput,
        testBidirectionalHighThroughput,
        testExtremeThroughput,
        testMultitransportsOneway,
        testMultitransportsBidirectional,
        testMultipleTransportsStressTest,
        stressTestV1,
        stressTestV2,
        stressTestV3,
        stressTestV4,
        multihostStresstestV1,
        multihostStresstestV2,
        multihostStresstestV3,
    ]
    num = args.num or 1
    # pylint: disable=unused-variable
    for i in range(num):
        for test in routines:
            test()
    print()
    success('All tests completed successfully')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automated testing for the socket.engine library')
    parser.add_argument('-n', '--num', help='The number of times each test should run', type=int)
    parser.add_argument('-d', '--debug', help='Turns on extra debugging messages', action='store_true')
    parser.add_argument(
        '-s', '--sleep', help='Sleep timer between actions (default {})'.format(DELAY), type=float,
    )
    arguments = parser.parse_args()
    main(arguments)
