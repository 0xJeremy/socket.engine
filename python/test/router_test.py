#!/usr/bin/env python3

import unittest
from socketengine import Router
from .common import (
    TIMEOUT,
    CHANNEL,
    TEST,
    TEST_2,
    PORT_TEST,
    PORT_TEST_2,
    HOME,
    TEXT,
    start,
    finish,
    initialize,
)

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def testRouterTransportSetup(self):
        start()
        routerOne = Router(timeout=TIMEOUT)
        routerTwo = Router(timeout=TIMEOUT)
        self.assertTrue(routerOne.opened)
        self.assertFalse(routerOne.stopped)
        self.assertTrue(routerTwo.opened)
        self.assertFalse(routerTwo.stopped)
        routerOne.connect(CHANNEL, HOME, routerTwo.port)
        routerOne.waitForTransport()
        routerTwo.waitForTransport()
        self.assertEqual(len(routerOne.transports), 1)
        self.assertEqual(len(routerTwo.transports), 1)
        routerOne.close()
        routerTwo.close()
        self.assertFalse(routerOne.opened)
        self.assertTrue(routerOne.stopped)
        self.assertFalse(routerTwo.opened)
        self.assertTrue(routerTwo.stopped)
        finish('Router Connection Setup Test Passed')

    def testTransportSetup(self):
        start()
        routerOne = Router(timeout=TIMEOUT)
        routerTwo = Router(timeout=TIMEOUT)
        routerOne.connect(CHANNEL, HOME, routerTwo.port)
        routerOne.waitForTransport()
        routerTwo.waitForTransport()
        self.assertEqual(len(routerOne.transports), 1)
        self.assertEqual(len(routerTwo.transports), 1)
        transportOne = routerOne.transports[0]
        transportTwo = routerTwo.transports[0]
        transportOne.waitForReady()
        transportTwo.waitForReady()
        self.assertTrue(transportOne.opened)
        self.assertFalse(transportOne.stopped)
        self.assertTrue(transportTwo.opened)
        self.assertFalse(transportTwo.stopped)
        transportTwo.waitForName()
        self.assertEqual(transportOne.name, CHANNEL)
        self.assertEqual(transportTwo.name, CHANNEL)
        self.assertEqual(transportOne.addr, HOME)
        self.assertEqual(transportTwo.addr, HOME)
        routerOne.close()
        routerTwo.close()
        self.assertFalse(transportOne.opened)
        self.assertTrue(transportOne.stopped)
        self.assertFalse(transportTwo.opened)
        self.assertTrue(transportTwo.stopped)
        finish('Connection Setup Test Passed')

    def testEmptyMessages(self):
        start()
        routerOne = Router(timeout=TIMEOUT)
        routerTwo = Router(timeout=TIMEOUT)
        self.assertEqual(routerOne.getAll(TEST), [])
        self.assertEqual(routerOne.getAll(TEST_2), [])
        self.assertEqual(routerTwo.getAll(TEST), [])
        self.assertEqual(routerTwo.getAll(TEST_2), [])
        routerOne.connect(TEST, HOME, routerTwo.port)
        routerTwo.waitForTransport()
        self.assertEqual(routerOne.getAll(TEST), [])
        self.assertEqual(routerOne.getAll(TEST_2), [])
        self.assertEqual(routerTwo.getAll(TEST), [])
        self.assertEqual(routerTwo.getAll(TEST_2), [])
        routerOne.close()
        routerTwo.close()
        finish('Empty messages Test Passed')

    def testOnewayMessages(self):
        start()
        routerOne = Router(timeout=TIMEOUT)
        routerTwo = Router(timeout=TIMEOUT)
        self.assertEqual(routerOne.getAll(TEST), [])
        self.assertEqual(routerOne.getAll(TEST_2), [])
        self.assertEqual(routerTwo.getAll(TEST), [])
        self.assertEqual(routerTwo.getAll(TEST_2), [])
        routerOne.connect(TEST, HOME, routerTwo.port)
        routerTwo.waitForTransport()
        routerOne.writeToNameWhenReady(TEST, TEST, PORT_TEST)
        routerTwo.waitForGetAll(TEST)
        self.assertEqual(routerOne.getAll(TEST), [])
        self.assertEqual(routerOne.getAll(TEST_2), [])
        self.assertEqual(routerTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(routerTwo.getAll(TEST_2), [])
        routerOne.writeToNameWhenReady(TEST, TEST_2, PORT_TEST_2)
        routerTwo.waitForGetAll(TEST_2)
        self.assertEqual(routerOne.getAll(TEST), [])
        self.assertEqual(routerOne.getAll(TEST_2), [])
        self.assertEqual(routerTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(routerTwo.getAll(TEST_2), [PORT_TEST_2])
        routerOne.close()
        routerTwo.close()
        finish('One-way messages Test Passed')

    def testBidirectionalMessages(self):
        start()
        routerOne, routerTwo = initialize()
        self.assertEqual(routerOne.getAll(TEST), [])
        self.assertEqual(routerOne.getAll(TEST_2), [])
        self.assertEqual(routerTwo.getAll(TEST), [])
        self.assertEqual(routerTwo.getAll(TEST_2), [])
        routerOne.writeToNameWhenReady(TEST, TEST, PORT_TEST)
        routerTwo.writeToNameWhenReady(TEST, TEST, PORT_TEST)
        routerOne.waitForGetAll(TEST)
        routerTwo.waitForGetAll(TEST)
        self.assertEqual(routerOne.getAll(TEST), [PORT_TEST])
        self.assertEqual(routerOne.getAll(TEST_2), [])
        self.assertEqual(routerTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(routerTwo.getAll(TEST_2), [])
        routerOne.writeToNameWhenReady(TEST, TEST_2, PORT_TEST_2)
        routerTwo.writeToNameWhenReady(TEST, TEST_2, PORT_TEST_2)
        routerOne.waitForGetAll(TEST_2)
        routerTwo.waitForGetAll(TEST_2)
        self.assertEqual(routerOne.getAll(TEST), [PORT_TEST])
        self.assertEqual(routerOne.getAll(TEST_2), [PORT_TEST_2])
        self.assertEqual(routerTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(routerTwo.getAll(TEST_2), [PORT_TEST_2])
        routerOne.close()
        routerTwo.close()
        finish('Bidirectional messages Test Passed')

    def stressHighSpeed(self, num=10, bidirectional=False, size=256):
        routerOne, routerTwo = initialize(size=size)
        for i in range(num):
            routerOne.writeToNameWhenReady(TEST, 'test{}'.format(i), TEXT)
            if bidirectional:
                routerTwo.writeToNameWhenReady(TEST, 'test{}'.format(i), TEXT)
        self.assertEqual(len(routerOne.transports), len(routerTwo.transports))

        for i in range(num):
            routerTwo.waitForGetAll('test{}'.format(i))
            if bidirectional:
                routerOne.waitForGetAll('test{}'.format(i))

        for i in range(num):
            if bidirectional:
                self.assertEqual(routerOne.getAll('test{}'.format(i)), [TEXT])
            self.assertEqual(routerTwo.getAll('test{}'.format(i)), [TEXT])
        routerOne.close()
        routerTwo.close()

    def testOnewayHighspeed(self):
        start()
        self.stressHighSpeed()
        finish('One-way High Speed Test Passed')

    def testBidirectionalHighspeed(self):
        start()
        self.stressHighSpeed(bidirectional=True)
        finish('Bidirectional High Speed Test Passed')

    # def testOnewayHighThroughput(self):
    #     start()
    #     self.stressHighSpeed(num=1000, size=2048)
    #     finish('One-way High Throughput Test Passed')

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

    def testMultitransportsOneway(self):
        start()
        self.multiTransports()
        finish('Multi-Connection One-Way Test Passed')

    def testMultitransportsBidirectional(self):
        start()
        self.multiTransports(bidirectional=True)
        finish('Multi-Connection Bidirectional Test Passed')


if __name__ == '__main__':
    unittest.main()
