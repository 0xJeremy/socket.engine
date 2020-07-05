#!/usr/bin/env python3

import unittest
from socketengine import Hub
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
    def testHubTransportSetup(self):
        start()
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
        self.assertTrue(hubOne.opened)
        self.assertFalse(hubOne.stopped)
        self.assertTrue(hubTwo.opened)
        self.assertFalse(hubTwo.stopped)
        hubOne.connect(CHANNEL, HOME, hubTwo.port)
        hubOne.waitForTransport()
        hubTwo.waitForTransport()
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
        hubOne.waitForTransport()
        hubTwo.waitForTransport()
        self.assertEqual(len(hubOne.transports), 1)
        self.assertEqual(len(hubTwo.transports), 1)
        transportOne = hubOne.transports[0]
        transportTwo = hubTwo.transports[0]
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
        hubOne.close()
        hubTwo.close()
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
        hubTwo.waitForTransport()
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
        hubTwo.waitForTransport()
        hubOne.writeToNameWhenReady(TEST, TEST, PORT_TEST)
        hubTwo.waitForGetAll(TEST)
        self.assertEqual(hubOne.getAll(TEST), [])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubTwo.getAll(TEST_2), [])
        hubOne.writeToNameWhenReady(TEST, TEST_2, PORT_TEST_2)
        hubTwo.waitForGetAll(TEST_2)
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
        hubOne.writeToNameWhenReady(TEST, TEST, PORT_TEST)
        hubTwo.writeToNameWhenReady(TEST, TEST, PORT_TEST)
        hubOne.waitForGetAll(TEST)
        hubTwo.waitForGetAll(TEST)
        self.assertEqual(hubOne.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubOne.getAll(TEST_2), [])
        self.assertEqual(hubTwo.getAll(TEST), [PORT_TEST])
        self.assertEqual(hubTwo.getAll(TEST_2), [])
        hubOne.writeToNameWhenReady(TEST, TEST_2, PORT_TEST_2)
        hubTwo.writeToNameWhenReady(TEST, TEST_2, PORT_TEST_2)
        hubOne.waitForGetAll(TEST_2)
        hubTwo.waitForGetAll(TEST_2)
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
            hubOne.writeToNameWhenReady(TEST, 'test{}'.format(i), TEXT)
            if bidirectional:
                hubTwo.writeToNameWhenReady(TEST, 'test{}'.format(i), TEXT)
        self.assertEqual(len(hubOne.transports), len(hubTwo.transports))

        for i in range(num):
            hubTwo.waitForGetAll('test{}'.format(i))
            if bidirectional:
                hubOne.waitForGetAll('test{}'.format(i))

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

    # def testOnewayHighThroughput(self):
    #     start()
    #     self.stressHighSpeed(num=1000, size=2048)
    #     finish('One-way High Throughput Test Passed')

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
