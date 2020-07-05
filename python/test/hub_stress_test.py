#!/usr/bin/env python3

import unittest
import time
from socketengine import Hub
from .common import TIMEOUT, HOME, TEXT, start, finish

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def multiTransports(self, numConn=10, messages=10, bidirectional=False, size=256):
        hubOne = Hub(timeout=TIMEOUT, size=size)
        hubTwo = Hub(timeout=TIMEOUT, size=size)
        for i in range(numConn):
            hubOne.connect('Test{}'.format(i), HOME, hubTwo.port)

        hubOne.waitForAllReady()
        hubTwo.waitForAllReady()

        for i in range(messages):
            hubOne.writeAllWhenReady('Test{}'.format(i), TEXT)
            if bidirectional:
                hubTwo.writeAllWhenReady('Test{}'.format(i), TEXT)

        hubTwo.waitForGetAll('Test{}'.format(messages - 1))
        if bidirectional:
            hubOne.waitForGetAll('Test{}'.format(messages - 1))

        for i in range(messages):
            if bidirectional:
                self.assertEqual(hubOne.getAll('Test{}'.format(i)), [TEXT] * numConn)
            self.assertEqual(hubTwo.getAll('Test{}'.format(i)), [TEXT] * numConn)
        hubOne.close()
        hubTwo.close()

    def testMultipleTransportsStressTest(self):
        start()
        self.multiTransports(numConn=25, messages=1000, bidirectional=True, size=2048)
        finish('Multi-Connection Stress Test Passed')

    # pylint: disable=too-many-branches
    def stressTest(self, stress=5, messages=1000):
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
        for i in range(stress):
            if i % 2 == 0:
                hubOne.connect('Test{}'.format(i), HOME, hubTwo.port)
            else:
                hubTwo.connect('Test{}'.format(i), HOME, hubOne.port)

        hubOne.waitForAllReady()
        hubTwo.waitForAllReady()
        self.assertEqual(len(hubOne.transports), len(hubTwo.transports))
        for i in range(messages):
            hubOne.writeAllWhenReady('Test{}'.format(i), TEXT)
            hubTwo.writeAllWhenReady('Test{}'.format(i), TEXT)

        for i in range(messages):
            time.sleep(0.01)
            hubOne.waitForGetAll('Test{}'.format(i))
            hubTwo.waitForGetAll('Test{}'.format(i))

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

    # def testStressTestV3(self):
    #     start()
    #     self.stressTest(stress=25)
    #     finish('Stress Test (v3) Passed')

    def multiHubStresstest(self, stress=5, messages=1000):
        hubs = []
        for i in range(stress):
            hub = Hub(timeout=TIMEOUT)
            hubs.append(hub)

        for hubOne in hubs:
            for hubTwo in hubs:
                hubTwo.connect('Test', HOME, hubOne.port)

        for hub in hubs:
            hub.waitForAllReady()
            self.assertEqual(len(hub.transports), 2 * stress)

        for hub in hubs:
            for i in range(messages):
                hub.writeAll('Test{}'.format(i), TEXT)

        for hub in hubs:
            hub.waitForGetAll('Test{}'.format(messages - 1))
            for i in range(messages):
                self.assertEqual(hub.getAll('Test{}'.format(i)), [TEXT] * 2 * stress)

        for hub in hubs:
            hub.close()

    def testMultihostStresstestV1(self):
        start()
        self.multiHubStresstest()
        finish('Multi-Host Stress Test (v1) Passed')

    def testMultihostStresstestV2(self):
        start()
        self.multiHubStresstest(stress=10)
        finish('Multi-Host Stress Test (v2) Passed')

    # def testMultihostStresstestV3(self):
    #     start()
    #     self.multiHubStresstest(stress=10, messages=5000)
    #     finish('Multi-Host Stress Test (v3) Passed')


if __name__ == '__main__':
    unittest.main()
