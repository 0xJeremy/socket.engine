from threading import Thread, Lock, Event
from zlib import compress, decompress
import time
import zmq
from google import protobuf
from .engine_commons import getUUID, getOpenPort, baseToPubSubPort
from .message_pb2 import SocketMessage

#################
### CONSTANTS ###
#################

from .constants import DELIMITER, ACK

CONN_REQUEST = b'portplease'

BASE_PORT = 8484

################################################################

#######################
### TRANSPORT CLASS ###
#######################

# pylint: disable=too-many-instance-attributes, fixme
class Transport:
    # pylint: disable=invalid-name
    DIRECT = 1
    SUBSCRIBER = 2
    BOTH = 3

    # pylint: disable=bad-continuation
    def __init__(
        self,
        context=zmq.Context(),
        # router=None,
        timeout=10,  # milliseconds
        compression=False,
        requireAcknowledgement=True,
        basePort=BASE_PORT,
    ):
        self.context = context
        # self.router = router # TODO: Add plugin capability
        self.timeout = timeout
        self.useCompression = compression
        self.requireAcknowledgement = requireAcknowledgement

        self.pairRoutingPort = basePort
        self.pubsubPort = baseToPubSubPort(basePort)

        self._topics = {}
        self._callbacks = {}
        self._topicEvents = {}
        self._awaitingAcknowledgement = {}

        self.parseLock = Lock()
        self._directConnectionsLock = Lock()
        self._closeEvent = Event()

        self._directConnections = {}
        self._routingSocket = None
        self._subscriber = None
        self._publisher = None
        self._pairHost = None

        self.stopped = False
        self.started = False

    ########################
    ### HELPER FUNCTIONS ###
    ########################

    def _generateBoundSocket(self, socketType, port):
        socket = self.context.socket(socketType)
        socket.RCVTIMEO = self.timeout  # in milliseconds
        socket.bind('tcp://*:{}'.format(port))
        return socket

    def _generateConnectSocket(self, socketType, address, port):
        socket = self.context.socket(socketType)
        socket.RCVTIMEO = self.timeout  # in milliseconds
        socket.connect('tcp://{}:{}'.format(address, port))
        return socket

    def _ensurePublisher(self):
        if self._publisher is not None:
            return
        # pylint: disable=no-member
        self._publisher = self._generateBoundSocket(zmq.PUB, self.pubsubPort)

    def _ensureSubscriber(self):
        if self._subscriber is not None:
            return
        # pylint: disable=no-member
        self._subscriber = self.context.socket(zmq.SUB)
        self._subscriber.RCVTIMEO = self.timeout  # in milliseconds

    def _connectSubscriber(self, address, port):
        # If the user specifies an override port, use that; otherwise use default
        port = port or self.pubsubPort
        self._subscriber.connect('tcp://{}:{}'.format(address, port))

    # Returns serialized string message
    def _createSocketMessage(self, topic, data, acknowledgement=False):
        message = SocketMessage()
        message.type = topic
        message.data = data
        if acknowledgement:
            message.acknowledge = True
            self._awaitingAcknowledgement[topic] = Event()
        serialized = message.SerializeToString()
        if self.useCompression:
            serialized = compress(serialized)
        return serialized

    ##########################
    ### CONNECTION HELPERS ###
    ##########################

    def _directConnect(self, address, targetBasePort):
        # TODO: Fix this behavior, appears (and is) fragile
        if self.pairRoutingPort is None:
            targetBasePort = self.pairRoutingPort

        socket = self._requestNewConnection(address, targetBasePort)
        uuid = getUUID()
        self._directConnections[uuid] = socket

        return uuid

    # pylint: disable=no-member
    def _requestNewConnection(self, address, port):
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

        openPort = getOpenPort()
        self._directConnections[getUUID()] = self._generateBoundSocket(zmq.PAIR, openPort)

        self._routingSocket.send_multipart(
            [address, b'', '{}'.format(openPort).encode(),]
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
                    self._handleMessage(message, socket)
                except zmq.error.Again:
                    pass

            if self._subscriber:
                try:
                    message = self._subscriber.recv()
                    self._handleSubscriptionMessage(message)
                except zmq.error.Again:
                    pass

    # pylint: disable=no-member
    def _handleMessage(self, rawMessage, socket=None):
        message = SocketMessage()
        try:
            message.ParseFromString(rawMessage)
        except protobuf.message.DecodeError:
            message.ParseFromString(decompress(rawMessage))
        # TODO: Implement metadata cascade
        # self._metadataCascade(message)

        # Parse message topic (type)
        if message.data != '':
            if message.data == ACK:
                if self._awaitingAcknowledgement.get(message.type, False):
                    self._awaitingAcknowledgement[message.type].set()
                    return
            self._topics[message.type] = message.data

        # Fire any registered callbacks
        if self._callbacks.get(message.type, False):
            self._callbacks[message.type](self, message.type, message.data)

        # Resolve any waiting events
        if self._topicEvents.get(message.type, False):
            self._topicEvents[message.type].set()

        # Send an acknowledgement if required
        # pylint: disable=singleton-comparison
        if message.acknowledge == True:
            self._sendAcknowledgement(socket, message.type)

    def _handleSubscriptionMessage(self, rawMessage):
        # TODO: Validate this approach
        self._handleMessage(rawMessage.split(DELIMITER)[1])

    def _sendMessage(self, message, routingID=None):
        if routingID is None:
            for socket in list(self._directConnections.values()):
                # TODO: This is not good, but makes things work. Invesgiate better methods.
                time.sleep(0.005)
                socket.send(message)
            return

        socket = self._directConnections[routingID]
        if socket is None:
            raise RuntimeError('Unable to send message to route ID; connection does not exist')
        socket.send(message)

    def _sendAcknowledgement(self, socket, topic):
        socket.send(self._createSocketMessage(topic, ACK))

    def _close(self):
        self.started = False
        for socket in list(self._directConnections.values()):
            socket.close()
        if self._publisher is not None:
            self._publisher.close()
        if self._subscriber is not None:
            self._subscriber.close()
        self._closeEvent.set()

    ######################
    ### CORE INTERFACE ###
    ######################

    def start(self):
        # Setup routing socket
        # This will sometimes fail with `zmq.error.ZMQError: Permission denied`
        # TODO: Add resiliance to this
        self._routingSocket = self._generateBoundSocket(zmq.ROUTER, self.pairRoutingPort)

        # Start thread
        Thread(target=self._run, args=()).start()
        self.started = True

        return self

    def connect(self, address, targetBasePort=None, connectionTypes=1):
        if not isinstance(connectionTypes, list):
            connectionTypes = [connectionTypes]

        uuid = None
        if Transport.DIRECT in connectionTypes:
            uuid = self._directConnect(address, targetBasePort)

        if Transport.SUBSCRIBER in connectionTypes:
            self._ensureSubscriber()
            self._connectSubscriber(address, targetBasePort)

        return uuid

    def publish(self, topic, data):
        # Ensure publisher exists, then push messages
        self._ensurePublisher()
        message = self._createSocketMessage(topic, data)
        self._publisher.send(topic.encode() + DELIMITER + message)

    def subscribe(self, topic):
        # Ensure a subscriber exists and subscribe
        self._ensureSubscriber()
        self._subscriber.subscribe(topic)

    def send(self, topic, data, routingID=None):
        self._sendMessage(
            self._createSocketMessage(topic, data, self.requireAcknowledgement), routingID
        )
        if self.requireAcknowledgement:
            self._awaitingAcknowledgement[topic].wait()

    def get(self, topic):
        return self._topics.get(topic, None)

    def registerCallback(self, topic, function):
        self._callbacks[topic] = function

    def close(self):
        self.stopped = True
        self._closeEvent.wait()

    #########################
    ### INTERFACE HELPERS ###
    #########################

    def waitForMessageOnTopic(self, topic):
        if self.get(topic) is not None:
            return
        self.waitForNewMessageOnTopic(topic)

    def waitForNewMessageOnTopic(self, topic):
        event = Event()
        self._topicEvents[topic] = event
        event.wait()
        self._topicEvents[topic] = None
