#!/usr/bin/env python3

import unittest
import time
from socketengine import Router
from .common import TIMEOUT, HOME, TEXT, start, finish

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def multiTransports(self, numConn=10, messages=10, bidirectional=False, size=256):
        routerOne = Router(timeout=TIMEOUT, size=size)
        routerTwo = Router(timeout=TIMEOUT, size=size)
        for i in range(numConn):
            routerOne.connect('Test{}'.format(i), HOME, routerTwo.port)

        routerOne.waitForAllReady()
        routerTwo.waitForAllReady()

        for i in range(messages):
            routerOne.writeAllWhenReady('Test{}'.format(i), TEXT)
            if bidirectional:
                routerTwo.writeAllWhenReady('Test{}'.format(i), TEXT)

        routerTwo.waitForGetAll('Test{}'.format(messages - 1))
        if bidirectional:
            routerOne.waitForGetAll('Test{}'.format(messages - 1))

        for i in range(messages):
            if bidirectional:
                self.assertEqual(routerOne.getAll('Test{}'.format(i)), [TEXT] * numConn)
            self.assertEqual(routerTwo.getAll('Test{}'.format(i)), [TEXT] * numConn)
        routerOne.close()
        routerTwo.close()

    def testMultipleTransportsStressTest(self):
        start()
        self.multiTransports(numConn=25, messages=1000, bidirectional=True, size=2048)
        finish('Multi-Connection Stress Test Passed')

    # pylint: disable=too-many-branches
    def stressTest(self, stress=5, messages=1000):
        routerOne = Router(timeout=TIMEOUT)
        routerTwo = Router(timeout=TIMEOUT)
        for i in range(stress):
            if i % 2 == 0:
                routerOne.connect('Test{}'.format(i), HOME, routerTwo.port)
            else:
                routerTwo.connect('Test{}'.format(i), HOME, routerOne.port)

        routerOne.waitForAllReady()
        routerTwo.waitForAllReady()
        self.assertEqual(len(routerOne.transports), len(routerTwo.transports))
        for i in range(messages):
            routerOne.writeAllWhenReady('Test{}'.format(i), TEXT)
            routerTwo.writeAllWhenReady('Test{}'.format(i), TEXT)

        for i in range(messages):
            time.sleep(0.01)
            routerOne.waitForGetAll('Test{}'.format(i))
            routerTwo.waitForGetAll('Test{}'.format(i))

        for i in range(messages):
            self.assertEqual(routerOne.getAll('Test{}'.format(i)), [TEXT] * stress)
            self.assertEqual(routerTwo.getAll('Test{}'.format(i)), [TEXT] * stress)
        routerOne.close()
        routerTwo.close()

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

    def multiRouterStresstest(self, stress=5, messages=1000):
        routers = []
        for i in range(stress):
            router = Router(timeout=TIMEOUT)
            routers.append(router)

        for routerOne in routers:
            for routerTwo in routers:
                routerTwo.connect('Test', HOME, routerOne.port)

        for router in routers:
            router.waitForAllReady()
            self.assertEqual(len(router.transports), 2 * stress)

        for router in routers:
            for i in range(messages):
                router.writeAll('Test{}'.format(i), TEXT)

        for router in routers:
            router.waitForGetAll('Test{}'.format(messages - 1))
            for i in range(messages):
                self.assertEqual(router.getAll('Test{}'.format(i)), [TEXT] * 2 * stress)

        for router in routers:
            router.close()

    def testMultihostStresstestV1(self):
        start()
        self.multiRouterStresstest()
        finish('Multi-Host Stress Test (v1) Passed')

    def testMultihostStresstestV2(self):
        start()
        self.multiRouterStresstest(stress=10)
        finish('Multi-Host Stress Test (v2) Passed')

    # def testMultihostStresstestV3(self):
    #     start()
    #     self.multiRouterStresstest(stress=10, messages=5000)
    #     finish('Multi-Host Stress Test (v3) Passed')


if __name__ == '__main__':
    unittest.main()
