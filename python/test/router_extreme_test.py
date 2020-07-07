#!/usr/bin/env python3

import unittest
import time
from socketengine import Router
from .common import TIMEOUT, TEST, HOME, TEXT, start, finish, initialize

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def stressHighSpeed(self, num=10, bidirectional=False, size=256):
        hubOne, hubTwo = initialize(size=size)
        for i in range(num):
            hubOne.writeToName(TEST, 'test{}'.format(i), TEXT)
            if bidirectional:
                hubTwo.writeToName(TEST, 'test{}'.format(i), TEXT)
        self.assertEqual(len(hubOne.transports), len(hubTwo.transports))

        for i in range(num):
            while hubTwo.getAll('test{}'.format(i)) != [TEXT]:
                time.sleep(0.01)
            if bidirectional:
                while hubOne.getAll('test{}'.format(i)) != [TEXT]:
                    time.sleep(0.01)

        for i in range(num):
            if bidirectional:
                self.assertEqual(hubOne.getAll('test{}'.format(i)), [TEXT])
            self.assertEqual(hubTwo.getAll('test{}'.format(i)), [TEXT])
        hubOne.close()
        hubTwo.close()

    def testBidirectionalHighThroughput(self):
        start()
        self.stressHighSpeed(num=1000, bidirectional=True, size=2048)
        finish('Bidirectional High Throughput Test Passed')

    def testExtremeThroughput(self):
        start()
        self.stressHighSpeed(num=5000, bidirectional=True, size=4096)
        finish('Extreme Throughput Test Passed')

    # pylint: disable=too-many-branches
    def multiTransports(self, numConn=10, messages=10, bidirectional=False, size=256):
        hubOne = Router(timeout=TIMEOUT, size=size)
        hubTwo = Router(timeout=TIMEOUT, size=size)
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

        for i in range(messages):
            while hubTwo.getAll('Test{}'.format(i)) != [TEXT] * numConn:
                time.sleep(0.1)
            if bidirectional:
                while hubOne.getAll('Test{}'.format(i)) != [TEXT] * numConn:
                    time.sleep(0.1)

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

    def testMultipleTransportsStressTest(self):
        start()
        self.multiTransports(numConn=25, messages=1000, bidirectional=True, size=2048)
        finish('Multi-Connection Stress Test Passed')

    def stressTest(self, stress=5, messages=1000):
        hubOne = Router(timeout=TIMEOUT)
        hubTwo = Router(timeout=TIMEOUT)
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

    def testStressTestV4(self):
        start()
        self.stressTest(stress=25, messages=5000)
        finish('Stress Test (v4) Passed')

    # pylint: disable=too-many-branches
    def multiRouterStresstest(self, stress=5, messages=1000):
        hubs = []
        for i in range(stress):
            hub = Router(timeout=TIMEOUT)
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

    def multihostStresstestV3(self):
        start()
        self.multiRouterStresstest(stress=10, messages=5000)
        finish('Multi-Host Stress Test (v3) Passed')

    # This test read/wrote 4.412gb of data in 818.95143 seconds. (on my machine)
    # It isn't worth running usually.
    # def multi_host_stressTestV4(self):
    #   start()
    #   self.multiRouterStresstest(stress=20, messages=5000)
    #   finish('Multi-Host Stress Test (v4)')


if __name__ == '__main__':
    unittest.main()
