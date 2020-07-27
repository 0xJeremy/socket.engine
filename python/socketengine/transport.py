import zmq
from threading import Thread, Lock, Event
from random import randint
from zlib import compress, decompress
from zlib import error as zlibError
from google import protobuf
from .engine_commons import encodeImg, decodeImg, generateSocket
from .message_pb2 import SocketMessage

#################
### CONSTANTS ###
#################

from .constants import ACK, IMAGE, DELIMITER, DELIMITER_SIZE

CONN_REQUEST = b'portplease'

BASE_PORT = 8484

################################################################

#######################
### TRANSPORT CLASS ###
#######################

# pylint: disable=invalid-name, consider-using-enumerate, no-member, too-many-instance-attributes, unused-variable
class Transport:
    DIRECT = 1
    SUBSCRIBER = 2
    BOTH = 3

    def __init__(
        self,
        context=zmq.Context(),
        # router=None,
        timeout=10,  # milliseconds
        compression=False,
        requireAcknowledgement=True,
        maximumDirectConnection=-1,
        maximumSubscriptions=-1,
        acceptIncomingConnections=True,
        willPublish=False,
        basePort=BASE_PORT,
    ):
        self.context = context
        # self.router = router # TODO: Add plugin capability
        self.timeout = timeout
        self.useCompression = compression
        self.requireAcknowledgement = requireAcknowledgement
        self.maximumDirectConnection = maximumDirectConnection
        self.maximumSubscriptions = maximumSubscriptions  # Maximum subscription sockets
        self.acceptIncomingConnections = acceptIncomingConnections
        self.willPublish = willPublish

        self.pubsubPort = basePort
        self.pairRoutingPort = basePort + 1
        self.currentPairPort = basePort + 2
        self.currentlyBoundPorts = []

        self._topics = {}
        self._callbacks = {}
        self._topicEvents = {}

        self.parseLock = Lock()
        self._directConnectionsLock = Lock()
        self._closeEvent = Event()

        self._directConnections = {}
        self._subscribers = []
        self._pairHost = None

        self.stopped = False
        self.started = False

    ########################
    ### HELPER FUNCTIONS ###
    ########################

    def _generateSocketUUID(self, n=5):
        uuid = randint(10 ** (n - 1), (10 ** n) - 1)
        while uuid in list(self._directConnections.keys()):
            uuid = randint(10 ** (n - 1), (10 ** n) - 1)
        return uuid

    def _generateBindSocket(self, type, port):
        socket = self.context.socket(type)
        socket.RCVTIMEO = self.timeout  # in milliseconds
        socket.bind('tcp://*:{}'.format(port))
        return socket

    def _generateConnectSocket(self, type, address, port):
        socket = self.context.socket(type)
        socket.RCVTIMEO = self.timeout  # in milliseconds
        socket.connect('tcp://{}:{}'.format(address, port))
        return socket

    def _ensureSubscriberExists(self):
        if self.subscriber is not None:
            return
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.RCVTIMEO = self.timeout  # in milliseconds

    def _openNewHostPair(self):
        if (
            self.maximumDirectConnection != -1
            and len(self._directConnections.values()) == self.maximumDirectConnection
        ):
            self._pairHost = None
            raise RuntimeError('Not opening new pair host; maximum limit met')
            return
        self._pairHost = self._generateBindSocket(zmq.PAIR, self.currentPairPort)
        self.currentlyBoundPorts.append(self.currentPairPort)
        self.currentPairPort += 1

    def _getUniquePort(self):
        while self.currentPairPort in self.currentlyBoundPorts:
            self.currentPairPort += 1
        return self.currentPairPort

    ##########################
    ### CONNECTION HELPERS ###
    ##########################

    def _directConnect(self, address, targetBasePort):
        # Fix this behavior, appears (and is) fragile
        targetBasePort = targetBasePort + 1 or self.pairRoutingPort

        if (
            self.maximumDirectConnection != -1
            and len(self._directConnections.values()) == self.maximumDirectConnection
        ):
            raise RuntimeError('Unable to connect to new remote; maximum limit met')

        socket = self._tryForNewConnection(address, targetBasePort)
        uuid = self._generateSocketUUID()
        self._directConnections[uuid] = socket

        return uuid

    def _tryForNewConnection(self, address, port):
        socket = self._generateConnectSocket(zmq.REQ, address, port)
        socket.send(CONN_REQUEST)
        # TODO: Better define this behavior
        while True:
            try:
                port = socket.recv().decode()
                break
            except zmq.error.Again:
                continue
        socket.close()
        return self._generateConnectSocket(zmq.PAIR, address, port)

    def _handleConnectionRequests(self, address, request):
        if request != CONN_REQUEST:
            raise RuntimeError('Received a connection request without appropriate metadata')

        portToUse = self._getUniquePort()
        socket = self._generateBindSocket(zmq.PAIR, self.currentPairPort)

        uuid = self._generateSocketUUID()
        self._directConnections[uuid] = socket

        self.currentlyBoundPorts.append(self.currentPairPort)

        self._routingSocket.send_multipart(
            [address, b'', '{}'.format(self.currentPairPort).encode(),]
        )

    #####################
    ### MAIN RUN LOOP ###
    #####################

    def _run(self):
        while True:
            if self.stopped:
                self._close()
                return

            try:
                address, _, request = self._routingSocket.recv_multipart()
                self._handleConnectionRequests(address, request)
            except zmq.error.Again:
                pass

            for socket in list(self._directConnections.values()):
                try:
                    message = socket.recv()
                    self._handleMessage(message)
                except zmq.error.Again:
                    pass

            for socket in self._subscribers:
                try:
                    message = socket.recv()
                    raise RuntimeError('Not implemented')  # TODO: Implement
                    self._handleSubscriptionMessage(message)
                except zmq.error.Again:
                    pass

    def _handleMessage(self, rawMessage):
        message = SocketMessage()
        message.ParseFromString(rawMessage)
        # TODO: Implement metadata cascade
        # self._metadataCascade(message)

        if message.type == IMAGE:
            self._topics[IMAGE] = decodeImg(message.data)
        elif message.data != '':
            self._topics[message.type] = message.data

        if self._callbacks.get(message.type, False):
            self._callbacks[message.type](self, message.type, message.data)

        if self._topicEvents.get(message.type, False):
            self._topicEvents[message.type].set()

    def _sendMessage(self, message, routingID):
        toSend = message.SerializeToString()
        if self.useCompression:
            toSend = compress(toSend)

        if routingID:
            socket = self._directConnections[routingID]
            if socket is None:
                raise RuntimeError('Unable to send message to route ID; connection does not exist')
            socket.send(toSend)
            return

        for socket in list(self._directConnections.values()):
            socket.send(toSend)

    def _close(self):
        self.started = False
        for socket in list(self._directConnections.values()):
            socket.close()
        if self._publisher is not None:
            self._publisher.close()
        for socket in self._subscribers:
            socket.close()
        self._closeEvent.set()

    ######################
    ### CORE INTERFACE ###
    ######################

    def start(self):
        if self.willPublish:
            self._publisher = self._generateBindSocket(zmq.PUB, self.pubsubPort)
            self.currentPairPort.append(self.pubsubPort)
        else:
            self._publisher = None

        # This will sometimes fail with `zmq.error.ZMQError: Permission denied`
        # TODO: Add resiliance to this
        self._routingSocket = self._generateBindSocket(zmq.ROUTER, self.pairRoutingPort)
        self.currentlyBoundPorts.append(self.pairRoutingPort)

        Thread(target=self._run, args=()).start()
        self.started = True
        return self

    def connect(self, address, targetBasePort=None, connectionType=1):
        uuid = None
        if connectionType in [Transport.DIRECT, Transport.BOTH]:
            uuid = self._directConnect(address, targetBasePort)

        if connectionType in [Transport.SUBSCRIBER, Transport.BOTH]:
            self._ensureSubscriberExists()
            self.subscriber.connect('tcp://{}:{}'.format(address, self.pubsubPort))

        return uuid

    def publish(self, topic, data):
        if not self.willPublish:
            raise RuntimeError(
                'Unable to publish message; configuration specifies Transport will not publish.'
            )
        message = SocketMessage()
        message.type = topic
        message.data = data
        toSend = message.SerializeToString()
        if self.compression:
            toSend = compress(toSend)

        self._publisher.send(topic.encode() + DELIMITER + toSend)

    def subscribe(self, topic):
        self._ensureSubscriberExists()
        self.subscriber.subscribe(topic)

    def send(self, topic, data, routingID=None):
        message = SocketMessage()
        message.type = topic
        message.data = data
        self._sendMessage(message, routingID)

    def get(self, topic):
        return self._topics.get(topic, None)

    def close(self):
        self.stopped = True
        self._closeEvent.wait()

    #########################
    ### INTERFACE HELPERS ###
    #########################

    def waitForMessageOnTopic(self, topic):
        if self.get(topic) is not None:
            return
        event = Event()
        self._topicEvents[topic] = event
        event.wait()
