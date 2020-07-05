#!/usr/bin/env python3

import unittest
from threading import Thread
import cv2
from socketengine import Transport
from .common import MESSAGE, CHANNEL, TEST, HOME, getUniquePort, start, finish

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def testConstructor(self):
        start()
        transport = Transport()
        self.assertFalse(transport.stopped)
        self.assertFalse(transport.opened)
        finish('Passed Constructor Test')

    def testWaitForConnection(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        transportOne.waitForOpen()
        transportTwo.waitForOpen()

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
        finish('Passed openForConnection')

    def testEmptyMessages(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        self.assertIsNone(transportOne.get(CHANNEL))
        self.assertIsNone(transportTwo.get(CHANNEL))

        transportOne.close()
        transportTwo.close()
        finish('Passed empty messages')

    def testNameAssignment(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        transportOne.waitForReady()
        transportTwo.waitForReady()

        self.assertIsNone(transportOne.name)
        self.assertIsNone(transportTwo.name)
        transportOne.assignName(TEST)
        transportTwo.waitForName()
        self.assertEqual(transportOne.name, TEST)
        self.assertEqual(transportTwo.name, TEST)

        transportOne.name = None
        transportTwo.name = None
        transportOne.nameEvent.clear()
        transportTwo.nameEvent.clear()

        self.assertIsNone(transportOne.name)
        self.assertIsNone(transportTwo.name)
        transportTwo.assignName(TEST)
        transportOne.waitForName()
        self.assertEqual(transportOne.name, TEST)
        self.assertEqual(transportTwo.name, TEST)

        transportOne.close()
        transportTwo.close()
        finish('Passed name assignment test')

    def testWriteAndGet(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        transportOne.waitForReady()
        transportTwo.waitForReady()
        transportOne.write(CHANNEL, MESSAGE)
        transportTwo.write(CHANNEL, MESSAGE)

        transportOne.waitForChannel(CHANNEL)
        transportTwo.waitForChannel(CHANNEL)

        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)
        self.assertTrue(transportOne.canWrite())
        self.assertTrue(transportTwo.canWrite())

        transportOne.close()
        transportTwo.close()
        finish('Passed write / get')

    def testWriteAndGetWithAck(self):
        start()
        transportOne = Transport(requireAck=True)
        transportTwo = Transport(requireAck=True)
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        transportOne.waitForReady()
        transportTwo.waitForReady()
        self.assertTrue(transportOne.canWrite())
        self.assertTrue(transportTwo.canWrite())
        transportOne.write(CHANNEL, MESSAGE)
        transportTwo.write(CHANNEL, MESSAGE)
        transportOne.waitForChannel(CHANNEL)
        transportTwo.waitForChannel(CHANNEL)
        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed write / get with ack')

    def testWriteAndGetWithwriteSync(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        transportOne.waitForReady()
        transportTwo.waitForReady()
        self.assertTrue(transportOne.canWrite())
        self.assertTrue(transportTwo.canWrite())
        transportOne.writeSync(CHANNEL, MESSAGE)
        transportTwo.writeSync(CHANNEL, MESSAGE)
        self.assertTrue(transportOne.canWrite())
        self.assertTrue(transportTwo.canWrite())
        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed write / get with writeSync ack')

    def testMessageCompression(self):
        start()
        transportOne = Transport(useCompression=True)
        transportTwo = Transport(useCompression=True)
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        transportOne.waitForReady()
        transportTwo.waitForReady()
        transportOne.write(CHANNEL, MESSAGE)
        transportTwo.write(CHANNEL, MESSAGE)
        transportOne.waitForChannel(CHANNEL)
        transportTwo.waitForChannel(CHANNEL)
        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed write / get with compression')

    # def testOneWayCloseRemote(self):
    #     start()
    #     transportOne = Transport()
    #     transportTwo = Transport()
    #     Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
    #     transportTwo.connect(HOME, transportOne.port)
    #     transportOne.close()
    #     transportOne.waitForClose()
    #     transportTwo.waitForClose()
    #     self.assertTrue(transportOne.stopped)
    #     self.assertFalse(transportOne.opened)
    #     self.assertTrue(transportTwo.stopped)
    #     self.assertFalse(transportTwo.opened)
    #     finish('Passed one way close (remote)')

    def testOneWayCloseLocal(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)
        transportTwo.close()
        transportOne.waitForClose()
        transportTwo.waitForClose()
        self.assertTrue(transportOne.stopped)
        self.assertFalse(transportOne.opened)
        self.assertTrue(transportTwo.stopped)
        self.assertFalse(transportTwo.opened)
        finish('Passed one way close (local)')

    def testImageWriteAndGet(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        # pylint: disable=no-member
        image = cv2.imread('test/beatles.jpg')
        transportTwo.writeImage(image)
        transportOne.waitForImage()
        self.assertTrue((transportOne.getImage() == image).all())
        transportOne.close()
        transportTwo.close()
        finish('Passed image write / get')

    def testImageWriteAndGetwithSync(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        # pylint: disable=no-member
        image = cv2.imread('test/beatles.jpg')
        transportTwo.writeImageSync(image)
        self.assertTrue((transportOne.getImage() == image).all())
        transportOne.close()
        transportTwo.close()
        finish('Passed image write / get with writeSync')

    def testImageWriteAndGetWithCompression(self):
        start()
        transportOne = Transport(useCompression=True)
        transportTwo = Transport(useCompression=True)
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)

        # pylint: disable=no-member
        image = cv2.imread('test/beatles.jpg')
        transportTwo.writeImage(image)
        transportOne.waitForImage()
        self.assertTrue((transportOne.getImage() == image).all())
        transportOne.close()
        transportTwo.close()
        finish('Passed image write / get with compression')

    def testRegisterCallback(self):
        start()
        transportOne = Transport()
        transportTwo = Transport()
        Thread(target=transportOne.openForConnection, args=[getUniquePort()]).start()
        transportTwo.connect(HOME, transportOne.port)
        transportOne.waitForReady()
        transportTwo.waitForReady()

        def callback(transport, channel, data):
            self.assertEqual(transport, transportOne)
            self.assertEqual(channel, CHANNEL)
            self.assertEqual(data, TEST)

        transportOne.registerCallback(CHANNEL, callback)
        transportTwo.write(CHANNEL, TEST)
        transportOne.close()
        transportTwo.close()
        finish('Passed callback registration')


if __name__ == '__main__':
    unittest.main()
