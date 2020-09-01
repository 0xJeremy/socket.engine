import zmq
import socket
from uuid import uuid4
from threading import Thread, Lock, Event
from random import randint
from zlib import compress, decompress
from zlib import error as zlibError
from google import protobuf
from .engine_commons import encodeImg, decodeImg
from .message_pb2 import SocketMessage

#################
### CONSTANTS ###
#################

from .constants import ACK, IMAGE, DELIMITER, DELIMITER_SIZE

CONN_REQUEST = b'portplease'

BASE_PORT = 8484

def getUUID():
    return str(uuid4())

# TODO: Make this less fragile? Use socket.bind_to_random_port with zmq?
def getOpenPort():
    sock = socket.socket()
    sock.bind(('', 0))

    _, port = sock.getsockname()
    sock.close()

    return port

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
        basePort=BASE_PORT,
    ):
        self.context = context
        # self.router = router # TODO: Add plugin capability
        self.timeout = timeout
        self.useCompression = compression
        self.requireAcknowledgement = requireAcknowledgement

        self.pairRoutingPort = basePort
        self.pubsubPort = basePort + 1

        self._topics = {}
        self._callbacks = {}
        self._topicEvents = {}

        self.parseLock = Lock()
        self._directConnectionsLock = Lock()
        self._closeEvent = Event()

        self._directConnections = {}
        self._subscriber = None
        self._publisher = None
        self._pairHost = None

        self.stopped = False
        self.started = False

    ########################
    ### HELPER FUNCTIONS ###
    ########################

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

    def _ensurePublisher(self):
        if self._publisher:
            return
        self._publisher = self._generateBindSocket(zmq.PUB, self.pubsubPort)

    def _ensureSubscriber(self):
        if self._subscriber is not None:
            return
        self._subscriber = self.context.socket(zmq.SUB)
        self._subscriber.RCVTIMEO = self.timeout  # in milliseconds

    # Returns serialized string message
    def createSocketMessage(self, topic, data):
        message = SocketMessage()
        message.type = topic
        message.data = data
        serialized = message.SerializeToString()
        if self.useCompression:
            serialized = compress(serialized)
        return serialized

    ##########################
    ### CONNECTION HELPERS ###
    ##########################

    def _directConnect(self, address, targetBasePort):
        # Fix this behavior, appears (and is) fragile
        if self.pairRoutingPort is None:
            targetBasePort = self.pairRoutingPort
        else:
            pass
            # targetBasePort += 1

        socket = self._requestNewConnection(address, targetBasePort)
        uuid = getUUID()
        self._directConnections[uuid] = socket

        return uuid

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
        socket = self._generateBindSocket(zmq.PAIR, openPort)

        self._directConnections[getUUID()] = socket

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
                    self._handleMessage(message)
                except zmq.error.Again:
                    pass

            if self._subscriber:
                try:
                    message = self._subscriber.recv()
                    self._handleSubscriptionMessage(message)
                except zmq.error.Again as err:
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

    def _handleSubscriptionMessage(self, rawMessage):
        # TODO: Validate this approach
        self._handleMessage(rawMessage.split(DELIMITER)[1])

    def _sendMessage(self, message, routingID):
        if routingID:
            socket = self._directConnections[routingID]
            if socket is None:
                raise RuntimeError('Unable to send message to route ID; connection does not exist')
            socket.send(message)
            return

        for socket in list(self._directConnections.values()):
            socket.send(message)

    def _close(self):
        self.started = False
        for socket in list(self._directConnections.values()):
            socket.close()
        if self._publisher is not None:
            self._publisher.close()
        if self._subscriber:
            self._subscriber.close()
        self._closeEvent.set()

    ######################
    ### CORE INTERFACE ###
    ######################

    def start(self):
        # Setup routing socket
        # This will sometimes fail with `zmq.error.ZMQError: Permission denied`
        # TODO: Add resiliance to this
        self._routingSocket = self._generateBindSocket(zmq.ROUTER, self.pairRoutingPort)

        # Start thread
        Thread(target=self._run, args=()).start()
        self.started = True

        return self

    def connect(self, address, targetBasePort=None, connectionType=1):
        uuid = None
        if connectionType in [Transport.DIRECT, Transport.BOTH]:
            uuid = self._directConnect(address, targetBasePort)

        if connectionType in [Transport.SUBSCRIBER, Transport.BOTH]:
            self._ensureSubscriber()
            self._subscriber.connect('tcp://{}:{}'.format(address, targetBasePort or self.pubsubPort))

        return uuid

    def publish(self, topic, data):
        # Ensure publisher exists, then push messages
        self._ensurePublisher()
        message = self.createSocketMessage(topic, data)
        self._publisher.send(topic.encode() + DELIMITER + message)

    def subscribe(self, topic):
        # Ensure a subscriber exists and subscribe
        self._ensureSubscriber()
        self._subscriber.subscribe(topic)

    def send(self, topic, data, routingID=None):
        self._sendMessage(self.createSocketMessage(topic, data), routingID)

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
