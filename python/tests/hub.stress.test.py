#!/usr/bin/env python3

import sys
import os
import unittest

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

# pylint: disable=wrong-import-position, no-member, too-many-branches, no-name-in-module, bad-continuation
from socketengine import Hub
from common import TIMEOUT, TEST, HOME, TEXT, start, finish, initialize

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def stressHighSpeed(self, num=10, bidirectional=False):
        hubOne, hubTwo = initialize()
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
        self.stressHighSpeed(num=1000)
        finish('One-way High Throughput Test Passed')

    def testBidirectionalHighThroughput(self):
        start()
        self.stressHighSpeed(num=1000, bidirectional=True)
        finish('Bidirectional High Throughput Test Passed')

    def testExtremeThroughput(self):
        start()
        self.stressHighSpeed(num=10000, bidirectional=True)
        finish('Extreme Throughput Test Passed')

    def multiTransports(self, numConn=10, messages=10, bidirectional=False):
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
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
            while hubTwo.getAll('Test{}'.format(messages - 1)) != [TEXT] * numConn:
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

    # def testMultitransportsBidirectional(self):
    #     start()
    #     self.multiTransports(bidirectional=True)
    #     finish('Multi-Connection Bidirectional Test Passed')

    # def testMultipleTransportsStressTest(self):
    #     start()
    #     self.multiTransports(numConn=25, messages=1000, bidirectional=True)
    #     finish('Multi-Connection Stress Test Passed')

    def stressTest(self, stress=5, messages=1000):
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
        for i in range(stress):
            if i % 2 == 0:
                hubOne.connect('Test{}'.format(i), HOME, hubTwo.port)
            else:
                hubTwo.connect('Test{}'.format(i), HOME, hubOne.port)

        while len(hubOne.transports) != len(hubTwo.transports):
            pass
        for transport in hubOne.transports:
            while not transport.opened:
                pass
        for transport in hubTwo.transports:
            while not transport.opened:
                pass

        self.assertEqual(len(hubOne.transports), len(hubTwo.transports))
        for i in range(messages):
            hubOne.writeAll('Test{}'.format(i), TEXT)
            hubTwo.writeAll('Test{}'.format(i), TEXT)
        while (
            hubOne.getAll('Test{}'.format(messages - 1)) != [TEXT] * stress
            or hubTwo.getAll('Test{}'.format(messages - 1)) != [TEXT] * stress
        ):
            pass

        for i in range(messages):
            self.assertEqual(hubOne.getAll('Test{}'.format(i)), [TEXT] * stress)
            self.assertEqual(hubTwo.getAll('Test{}'.format(i)), [TEXT] * stress)
        hubOne.close()
        hubTwo.close()

    def testStressTestV1(self):
        start()
        self.stressTest()
        finish('Stress Test (v1) Passed')

    def testStressTestV2(self):
        start()
        self.stressTest(stress=10)
        finish('Stress Test (v2) Passed')

    def testStressTestV3(self):
        start()
        self.stressTest(stress=25)
        finish('Stress Test (v3) Passed')

    def testStressTestV4(self):
        start()
        self.stressTest(stress=25, messages=5000)
        finish('Stress Test (v4) Passed')

    def multiHubStresstest(self, stress=5, messages=1000):
        hubs = []
        for i in range(stress):
            hub = Hub(timeout=TIMEOUT)
            hubs.append(hub)

        for hubOne in hubs:
            for hubTwo in hubs:
                hubTwo.connect('Test', HOME, hubOne.port)

        for hub in hubs:
            for transport in hub.transports:
                while not transport.opened:
                    pass
            while len(hub.transports) != 2 * stress:
                pass

        for hub in hubs:
            self.assertEqual(len(hub.transports), 2 * stress)

        for hub in hubs:
            for i in range(messages):
                hub.writeAll('Test{}'.format(i), TEXT)

        for hub in hubs:
            while hub.getAll('Test{}'.format(messages - 1)) != [TEXT] * 2 * stress:
                pass

        for hub in hubs:
            for i in range(messages):
                self.assertEqual(hub.getAll('Test{}'.format(i)), [TEXT] * 2 * stress)

        for hub in hubs:
            hub.close()

    def testMultihostStresstestV1(self):
        start()
        self.multiHubStresstest()
        finish('Multi-Host Stress Test (v1) Passed')

    def multihostStresstestV2(self):
        start()
        self.multiHubStresstest(stress=10)
        finish('Multi-Host Stress Test (v2) Passed')

    def multihostStresstestV3(self):
        start()
        self.multiHubStresstest(stress=10, messages=5000)
        finish('Multi-Host Stress Test (v3) Passed')

    # This test read/wrote 4.412gb of data in 818.95143 seconds. (on my machine)
    # It isn't worth running usually.
    # def multi_host_stressTestV4(self):
    #   start()
    #   self.multiHubStresstest(stress=20, messages=5000)
    #   finish('Multi-Host Stress Test (v4)')


if __name__ == '__main__':
    unittest.main()
