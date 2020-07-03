#!/usr/bin/env python3

import sys
import os
import unittest

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

# pylint: disable=wrong-import-position, no-member, too-many-branches, no-name-in-module
from socketengine import Hub
from common import TIMEOUT, CHANNEL, TEST, TEST_2, PORT_TEST, PORT_TEST_2, HOME, TEXT, start, finish, initialize

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def testHubTransportSetup(self):
        start()
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
        self.assertTrue(hubOne.opened)
        self.assertFalse(hubOne.stopped)
        self.assertTrue(hubTwo.opened)
        self.assertFalse(hubTwo.stopped)
        hubOne.connect(CHANNEL, HOME, hubTwo.port)
        while len(hubOne.transports) == 0 or len(hubTwo.transports) == 0:
            pass
        self.assertEqual(len(hubOne.transports), 1)
        self.assertEqual(len(hubTwo.transports), 1)
        hubOne.close()
        hubTwo.close()
        self.assertFalse(hubOne.opened)
        self.assertTrue(hubOne.stopped)
        self.assertFalse(hubTwo.opened)
        self.assertTrue(hubTwo.stopped)
        finish('Hub Connection Setup Test Passed')

    def testTransportSetup(self):
        start()
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
        hubOne.connect(CHANNEL, HOME, hubTwo.port)
        while len(hubOne.transports) == 0 or len(hubTwo.transports) == 0:
            pass
        self.assertEqual(len(hubOne.transports), 1)
        self.assertEqual(len(hubTwo.transports), 1)
        transportOne = hubOne.transports[0]
        transportTwo = hubTwo.transports[0]
        while transportOne.stopped or transportTwo.stopped:
            pass
        self.assertTrue(transportOne.opened)
        self.assertFalse(transportOne.stopped)
        self.assertTrue(transportTwo.opened)
        self.assertFalse(transportTwo.stopped)
        while not transportOne.name or not transportTwo.name:
            pass
        self.assertEqual(transportOne.name, CHANNEL)
        self.assertEqual(transportTwo.name, CHANNEL)
        self.assertEqual(transportOne.addr, HOME)
        self.assertEqual(transportTwo.addr, HOME)
        hubOne.close()
        hubTwo.close()
        while transportOne.opened or transportTwo.opened:
            pass
        self.assertFalse(transportOne.opened)
        self.assertTrue(transportOne.stopped)
        self.assertFalse(transportTwo.opened)
        self.assertTrue(transportTwo.stopped)
        finish('Connection Setup Test Passed')

    def testEmptyMessages(self):
        start()
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
        self.assertEqual(hubOne.getAll(TEST), [])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [])
        self.assertEqual(hubTwo.getAll(TEST_2), [])
        hubOne.connect(TEST, HOME, hubTwo.port)
        while len(hubTwo.transports) == 0:
            pass
        self.assertEqual(hubOne.getAll(TEST), [])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [])
        self.assertEqual(hubTwo.getAll(TEST_2), [])
        hubOne.close()
        hubTwo.close()
        finish('Empty messages Test Passed')

    def testOnewayMessages(self):
        start()
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
        self.assertEqual(hubOne.getAll(TEST), [])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [])
        self.assertEqual(hubTwo.getAll(TEST_2), [])
        hubOne.connect(TEST, HOME, hubTwo.port)
        while len(hubTwo.transports) == 0:
            pass
        hubOne.writeToName(TEST, TEST, PORT_TEST)
        while hubTwo.getAll(TEST) == []:
            pass
        self.assertEqual(hubOne.getAll(TEST), [])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubTwo.getAll(TEST_2), [])
        hubOne.writeToName(TEST, TEST_2, PORT_TEST_2)
        while hubTwo.getAll(TEST_2) == []:
            pass
        self.assertEqual(hubOne.getAll(TEST), [])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubTwo.getAll(TEST_2), [PORT_TEST_2])
        hubOne.close()
        hubTwo.close()
        finish('One-way messages Test Passed')

    def testBidirectionalMessages(self):
        start()
        hubOne, hubTwo = initialize()
        self.assertEqual(hubOne.getAll(TEST), [])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [])
        self.assertEqual(hubTwo.getAll(TEST_2), [])
        hubOne.writeToName(TEST, TEST, PORT_TEST)
        hubTwo.writeToName(TEST, TEST, PORT_TEST)
        while hubOne.getAll(TEST) == [] or hubTwo.getAll(TEST) == []:
            pass
        self.assertEqual(hubOne.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubTwo.getAll(TEST_2), [])
        hubOne.writeToName(TEST, TEST_2, PORT_TEST_2)
        hubTwo.writeToName(TEST, TEST_2, PORT_TEST_2)
        while hubOne.getAll(TEST_2) == [] or hubTwo.getAll(TEST_2) == []:
            pass
        self.assertEqual(hubOne.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubOne.getAll(TEST_2), [PORT_TEST_2])
        self.assertEqual(hubTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubTwo.getAll(TEST_2), [PORT_TEST_2])
        hubOne.close()
        hubTwo.close()
        finish('Bidirectional messages Test Passed')

    def stressHighSpeed(self, num=10, bidirectional=False, size=256):
        hubOne, hubTwo = initialize(size=size)
        for i in range(num):
            hubOne.writeToName(TEST, 'test{}'.format(i), TEXT)
            if bidirectional:
                hubTwo.writeToName(TEST, 'test{}'.format(i), TEXT)
        self.assertEqual(len(hubOne.transports), len(hubTwo.transports))
        while hubTwo.getAll('test{}'.format(num - 1)) == []:
            pass
        if bidirectional:
            while hubOne.getAll('test{}'.format(num - 1)) == []:
                pass
        for i in range(num):
            if bidirectional:
                self.assertEqual(hubOne.getAll('test{}'.format(i)), [TEXT])
            self.assertEqual(hubTwo.getAll('test{}'.format(i)), [TEXT])
        hubOne.close()
        hubTwo.close()

    def testOnewayHighspeed(self):
        start()
        self.stressHighSpeed()
        finish('One-way High Speed Test Passed')

    def testBidirectionalHighspeed(self):
        start()
        self.stressHighSpeed(bidirectional=True)
        finish('Bidirectional High Speed Test Passed')

    def testOnewayHighThroughput(self):
        start()
        self.stressHighSpeed(num=1000, size=2048)
        finish('One-way High Throughput Test Passed')

    def multiTransports(self, numConn=10, messages=10, bidirectional=False, size=256):
        hubOne = Hub(timeout=TIMEOUT, size=size)
        hubTwo = Hub(timeout=TIMEOUT, size=size)
        for i in range(numConn):
            hubOne.connect('Test{}'.format(i), HOME, hubTwo.port)

        while len(hubOne.transports) != len(hubTwo.transports):
            pass
        for transport in hubOne.transports:
            while not transport.opened:
                pass
        for transport in hubTwo.transports:
            while not transport.opened:
                pass

        for i in range(messages):
            hubOne.writeAll('Test{}'.format(i), TEXT)
            if bidirectional:
                hubTwo.writeAll('Test{}'.format(i), TEXT)

        while hubTwo.getAll('Test{}'.format(messages - 1)) != [TEXT] * numConn:
            pass
        if bidirectional:
            while hubOne.getAll('Test{}'.format(messages - 1)) != [TEXT] * numConn:
                pass

        for i in range(messages):
            if bidirectional:
                self.assertEqual(hubOne.getAll('Test{}'.format(i)), [TEXT] * numConn)
            self.assertEqual(hubTwo.getAll('Test{}'.format(i)), [TEXT] * numConn)
        hubOne.close()
        hubTwo.close()

    def testMultitransportsOneway(self):
        start()
        self.multiTransports()
        finish('Multi-Connection One-Way Test Passed')

    def testMultitransportsBidirectional(self):
        start()
        self.multiTransports(bidirectional=True, size=2048)
        finish('Multi-Connection Bidirectional Test Passed')


if __name__ == '__main__':
    unittest.main()
