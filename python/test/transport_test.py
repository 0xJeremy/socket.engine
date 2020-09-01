#!/usr/bin/env python3

import unittest
import time
from random import randint
import zmq
from socketengine import Transport
from .common import MESSAGE, CHANNEL, getUniquePort, start, finish

# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def testConstructor(self):
        start()
        transport = Transport()

        self.assertFalse(transport.stopped)
        self.assertFalse(transport.started)
        transport.start()
        self.assertFalse(transport.stopped)
        self.assertTrue(transport.started)
        transport.close()
        self.assertTrue(transport.stopped)
        self.assertFalse(transport.started)

        finish('Passed Constructor and Start Test')

    def testPortBinding(self):
        start()

        transport = Transport().start()
        context = zmq.Context()
        # pylint: disable=no-member
        socket = context.socket(zmq.PAIR)

        def bindSocket():
            socket.bind('tcp://*:8484')

        self.assertRaises(zmq.error.ZMQError, bindSocket)

        transport.close()

        finish('Passed port binding test')

    def testPortChanging(self):
        start()
        port = 5000

        transport = Transport(basePort=port).start()
        context = zmq.Context()
        # pylint: disable=no-member
        socket = context.socket(zmq.PAIR)

        def bindSocket():
            socket.bind('tcp://*:{}'.format(port))

        self.assertRaises(zmq.error.ZMQError, bindSocket)

        transport.close()

        finish('Passed base port changing test')

    def testPublisherPortBinding(self):
        start()
        port = 5000

        transport = Transport(basePort=port).start()
        context = zmq.Context()
        # pylint: disable=no-member
        socket = context.socket(zmq.PAIR)
        transport.publish('test', 'testing')

        def bindSocket():
            socket.bind('tcp://*:{}'.format(port))

        self.assertRaises(zmq.error.ZMQError, bindSocket)

        def bindPubSubSocket():
            socket.bind('tcp://*:{}'.format(port + 1))

        self.assertRaises(zmq.error.ZMQError, bindSocket)

        transport.close()

        finish('Passed pub/sub port binding')

    def testPortCollision(self):
        start()

        transportOne = Transport().start()
        transportTwo = Transport()
        self.assertRaises(zmq.error.ZMQError, transportTwo.start)
        transportOne.close()

        finish('Passed Port Collision')

    def testAutoConnection(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        # pylint: disable=protected-access
        self.assertEqual(len(transportOne._directConnections), 1)
        self.assertEqual(len(transportTwo._directConnections), 1)

        transportOne.close()
        transportTwo.close()
        finish('Passed Auto Connection')

    def testAutoConnectionMultiple(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne)
        transportTwo = Transport(basePort=portTwo)

        transportOne.start()
        transportTwo.start()

        numConnections = 10
        for i in range(numConnections):
            transportOne.connect('127.0.0.1', targetBasePort=portTwo)
            transportTwo.connect('127.0.0.1', targetBasePort=portOne)

        # pylint: disable=protected-access
        self.assertEqual(len(transportOne._directConnections), numConnections * 2)
        self.assertEqual(len(transportTwo._directConnections), numConnections * 2)

        transportOne.close()
        transportTwo.close()
        finish('Passed Auto-Connect Multiple')

    def testEmptyMessages(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        self.assertIsNone(transportOne.get(CHANNEL))
        self.assertIsNone(transportTwo.get(CHANNEL))

        transportOne.close()
        transportTwo.close()
        finish('Passed empty messages')

    def testWriteAndGet(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        transportOne.send(CHANNEL, MESSAGE)
        transportTwo.send(CHANNEL, MESSAGE)

        transportOne.waitForMessageOnTopic(CHANNEL)
        transportTwo.waitForMessageOnTopic(CHANNEL)

        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed write / get')

    def testMultiWriteAndGet(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        for i in range(40):
            channel = str(randint(1000, 100000))
            message = str(randint(1000, 100000))

            transportOne.send(channel, message)
            transportTwo.send(channel, message)

            transportOne.waitForMessageOnTopic(channel)
            transportTwo.waitForMessageOnTopic(channel)

            self.assertEqual(transportOne.get(channel), message)
            self.assertEqual(transportTwo.get(channel), message)

        transportOne.close()
        transportTwo.close()
        finish('Passed multi- write / get')

    def testWriteWithRoutingID(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        routingID = transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        transportOne.send(CHANNEL, MESSAGE, routingID=routingID)
        transportTwo.waitForMessageOnTopic(CHANNEL)

        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed write with routing ID')

    def testMultipleRoutingIDs(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        for i in range(10):
            channel = str(randint(1000, 100000))
            message = str(randint(1000, 100000))

            routingID = transportOne.connect('127.0.0.1', targetBasePort=portTwo)

            transportOne.send(channel, message, routingID=routingID)
            transportTwo.waitForMessageOnTopic(channel)

            self.assertEqual(transportTwo.get(channel), message)

        transportOne.close()
        transportTwo.close()
        finish('Passed write with multiple routing IDs')

    def testPublishSubscribe(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        transportOne.connect(
            '127.0.0.1', targetBasePort=portTwo + 1, connectionTypes=Transport.SUBSCRIBER
        )
        transportOne.subscribe(CHANNEL)

        while transportOne.get(CHANNEL) is None:
            time.sleep(0.05)
            transportTwo.publish(CHANNEL, MESSAGE)

        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed publish / subscribe')

    def testMultiPublishSubscribe(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        transportOne.connect(
            '127.0.0.1', targetBasePort=portTwo + 1, connectionTypes=Transport.SUBSCRIBER
        )

        for i in range(10):
            channel = str(randint(1000, 100000))
            message = str(randint(1000, 100000))

            transportOne.subscribe(channel)

            while transportOne.get(channel) is None:
                time.sleep(0.05)
                transportTwo.publish(channel, message)

            self.assertEqual(transportOne.get(channel), message)

        transportOne.close()
        transportTwo.close()
        finish('Passed multiple publish / subscribe')

    def testMultipleConnections(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        portThree = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()
        transportThree = Transport(basePort=portThree).start()

        routingID = transportOne.connect('127.0.0.1', targetBasePort=portTwo)
        routingIDTwo = transportThree.connect('127.0.0.1', targetBasePort=portTwo)

        for i in range(20):
            channelOne = str(randint(1000, 100000))
            messageOne = str(randint(1000, 100000))

            channelTwo = str(randint(1000, 100000))
            messageTwo = str(randint(1000, 100000))

            transportOne.send(channelOne, messageOne, routingID=routingID)

            transportThree.send(channelTwo, messageTwo, routingID=routingIDTwo)

            transportTwo.waitForMessageOnTopic(channelOne)
            self.assertEqual(transportTwo.get(channelOne), messageOne)

            transportTwo.waitForMessageOnTopic(channelTwo)
            self.assertEqual(transportTwo.get(channelTwo), messageTwo)

        transportOne.close()
        transportTwo.close()
        transportThree.close()

        finish('Passed write with routing ID and multiple transports')

    def testRequireAcknowledgement(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne, requireAcknowledgement=True).start()
        transportTwo = Transport(basePort=portTwo, requireAcknowledgement=True).start()

        transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        transportOne.send(CHANNEL, MESSAGE)
        transportTwo.send(CHANNEL, MESSAGE)

        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed write / get with acknowledgement')

    def testMultipleRequireAcknowledgement(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne, requireAcknowledgement=True).start()
        transportTwo = Transport(basePort=portTwo, requireAcknowledgement=True).start()

        transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        for i in range(20):
            channel = str(randint(1000, 100000))
            message = str(randint(1000, 100000))

            transportOne.send(channel, message)
            transportTwo.send(channel, message)

            self.assertEqual(transportOne.get(channel), message)
            self.assertEqual(transportTwo.get(channel), message)

        transportOne.close()
        transportTwo.close()
        finish('Passed multiple write / get with acknowledgement')

    def testCallbackRegistration(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne).start()
        transportTwo = Transport(basePort=portTwo).start()

        transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        # pylint: disable=attribute-defined-outside-init
        self.callbackTriggered = False

        def exampleCallback(transport, topic, data):
            self.assertEqual(transport, transportOne)
            self.assertEqual(topic, CHANNEL)
            self.assertEqual(data, MESSAGE)
            self.callbackTriggered = True

        transportOne.registerCallback(CHANNEL, exampleCallback)

        transportTwo.send(CHANNEL, MESSAGE)
        transportOne.waitForMessageOnTopic(CHANNEL)
        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertTrue(self.callbackTriggered)

        transportOne.close()
        transportTwo.close()

        finish('Passed callback registration')

    def testMessageCompression(self):
        start()

        portOne = getUniquePort()
        portTwo = getUniquePort()
        transportOne = Transport(basePort=portOne, compression=True).start()
        transportTwo = Transport(basePort=portTwo, compression=True).start()

        transportOne.connect('127.0.0.1', targetBasePort=portTwo)

        transportOne.send(CHANNEL, MESSAGE)
        transportTwo.send(CHANNEL, MESSAGE)

        transportOne.waitForMessageOnTopic(CHANNEL)
        transportTwo.waitForMessageOnTopic(CHANNEL)

        self.assertEqual(transportOne.get(CHANNEL), MESSAGE)
        self.assertEqual(transportTwo.get(CHANNEL), MESSAGE)

        transportOne.close()
        transportTwo.close()
        finish('Passed write / get with compression')


if __name__ == '__main__':
    unittest.main()
