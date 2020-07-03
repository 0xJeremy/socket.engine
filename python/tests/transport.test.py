#!/usr/bin/env python3

import sys
import os
import unittest
from threading import Thread
import time
import cv2

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

# pylint: disable=wrong-import-position, no-member, too-many-branches, no-name-in-module, bad-continuation
from socketengine import Transport
from common import MESSAGE, CHANNEL, TEST, HOME, getUniquePort, start, finish

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def testConstructor(self):
        start()
        transport = Transport()
        self.assertTrue(transport.canWrite)
        self.assertFalse(transport.stopped)
        self.assertFalse(transport.opened)
        finish('Passed Constructor Test')

    def testWaitForConnection(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.waitForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(TEST, HOME, transportOne.port)
        while not transportOne.opened:
            pass
        self.assertTrue(transportOne.opened)
        self.assertFalse(transportOne.stopped)
        self.assertEqual(transportOne.type, Transport.TYPE_REMOTE)
        self.assertTrue(transportTwo.opened)
        self.assertFalse(transportTwo.stopped)
        self.assertEqual(transportTwo.type, Transport.TYPE_LOCAL)
        transportOne.close()
        transportTwo.close()
        self.assertFalse(transportOne.opened)
        self.assertTrue(transportOne.stopped)
        self.assertFalse(transportTwo.opened)
        self.assertTrue(transportTwo.stopped)
        finish('Passed waitForConnection')

    def testEmptyMessages(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.waitForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(TEST, HOME, transportOne.port)

        self.assertEqual(transportOne.get(CHANNEL), None)
        self.assertEqual(transportTwo.get(CHANNEL), None)

        transportOne.close()
        transportTwo.close()
        finish('Passed empty messages')

    def testWriteAndGet(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.waitForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(TEST, HOME, transportOne.port)

        transportOne.write(CHANNEL, MESSAGE)
        transportTwo.write(CHANNEL, MESSAGE)
        while transportOne.get(CHANNEL) is None or transportTwo.get(CHANNEL) is None:
            continue
        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed write / get')

    def testOneWayCloseRemote(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.waitForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(TEST, HOME, transportOne.port)
        transportOne.close()
        while transportOne.opened or transportTwo.opened:
            pass
        self.assertTrue(transportOne.stopped)
        self.assertFalse(transportOne.opened)
        self.assertTrue(transportTwo.stopped)
        self.assertFalse(transportTwo.opened)
        finish('Passed one way close (remote)')

    def testOneWayCloseLocal(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.waitForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(TEST, HOME, transportOne.port)
        transportTwo.close()
        while transportOne.opened or transportTwo.opened:
            pass
        self.assertTrue(transportOne.stopped)
        self.assertFalse(transportOne.opened)
        self.assertTrue(transportTwo.stopped)
        self.assertFalse(transportTwo.opened)
        finish('Passed one way close (local)')

    def testImageWriteAndGet(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.waitForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(TEST, HOME, transportOne.port)

        image = cv2.imread('beatles.jpg')
        transportTwo.writeImage(image)
        while transportOne.getImage() is None:
            time.sleep(0.01)
        self.assertTrue((transportOne.getImage() == image).all())
        transportOne.close()
        transportTwo.close()
        finish('Passed image write / get')


if __name__ == '__main__':
    unittest.main()
