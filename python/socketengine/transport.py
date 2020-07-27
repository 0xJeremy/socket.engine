import socket
from threading import Thread, Lock, Event
from random import randint
from zlib import compress, decompress
from zlib import error as zlibError
from google import protobuf
from .engine_commons import encodeImg, decodeImg, generateSocket
from .message_pb2 import SocketMessage
import zmq

#################
### CONSTANTS ###
#################

from .constants import ACK, IMAGE, TIMEOUT, SIZE, CLOSING
from .constants import DELIMITER, DELIMITER_SIZE

CONN_REQUEST = b'portplease'

PUBSUB_PORT = 8484
PAIR_ROUTING_PORT = 8485

BASE_PORT = 8484

################################################################

#######################
### TRANSPORT CLASS ###
#######################

# pylint: disable=invalid-name, consider-using-enumerate, no-member, too-many-instance-attributes, unused-variable
class Transport:
    def __init__(
        self,
        context=zmq.Context(),
        # router=None,
        timeout=1000, # milliseconds
        compression=False,
        requireAcknowledgement=True,
        maximumDirectConnection=-1,
        maximumSubscriptions=-1,
        acceptIncomingConnections=True,
        willPublish=False,
        basePort=8484
    ):
        self.context = context
        # self.router = router # TODO: Add plugin capability
        self.timeout = timeout
        self.useCompression = compression
        self.requireAcknowledgement = requireAcknowledgement
        self.maximumDirectConnection = maximumDirectConnection
        self.maximumSubscriptions = maximumSubscriptions # Maximum subscription sockets
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
        self.closeEvent = Event()

        self._directConnections = {}
        self._subscribers = []
        self._pairHost = None

        self.stopped = False
        self.started = False

    ########################
    ### HELPER FUNCTIONS ###
    ########################

    def _generateSocketUUID(self, n=5):
        uuid = randint(10**(n-1), (10**n)-1)
        with self._directConnectionsLock:
            while uuid in self._directConnections.keys():
                uuid = randint(10**(n-1), (10**n)-1)
        return uuid

    def _generateBindSocket(self, type, port):
        socket = self.context.socket(type)
        socket.RCVTIMEO = self.timeout # in milliseconds
        socket.bind('tcp://*:{}'.format(port))
        return socket

    def _generateConnectSocket(self, type, address, port):
        socket = self.context.socket(type)
        socket.RCVTIMEO = self.timeout # in milliseconds
        socket.connect('tcp://{}:{}'.format(address, port))
        return socket

    def _openNewHostPair(self):
        if self.maximumDirectConnection != -1 and len(self._directConnections.values()) == self.maximumDirectConnection:
            self._pairHost = None
            raise RuntimeError('Not opening new pair host; maximum limit met')
            return
        self._pairHost = self._generateBindSocket(zmq.PAIR, self.currentPairPort)
        self.currentlyBoundPorts.append(self.currentPairPort)
        self.currentPairPort += 1
        return

    #########################
    ### CONNECT TO REMOTE ###
    #########################

    def connect(self, address, targetBasePort=None, connectToPublisher=False):
        # Fix this behavior, appears (and is) fragile
        targetBasePort = targetBasePort + 1 or self.pairRoutingPort
        print("targeting", targetBasePort)
        if self.maximumDirectConnection != -1 and len(self._directConnections.values()) == self.maximumDirectConnection:
            raise RuntimeError('Unable to connect to new remote; maximum limit met')

        socket = self._tryForNewConnection(address, targetBasePort)
        socketUUID = self._generateSocketUUID()

        with self._directConnectionsLock:
            self._directConnections[socketUUID] = socket

        if connectToPublisher:
            self._connectToPublisher(address)

        return socketUUID

    def _connectToPublisher(self, address):
        if self.subscriber is None:
            self.subscriber = self._generateConnectSocket(zmq.SUB, address, self.pubsubPort)
        else:
            self.subscriber.connect('tcp://{}:{}'.format(address, self.pubsubPort))

    def _tryForNewConnection(self, address, port):
        socket = self._generateConnectSocket(zmq.REQ, address, port)
        print("sending CONN_REQUEST to port", port)
        socket.send(CONN_REQUEST)
        # TODO: Better define this behavior
        while True:
            try:
                port = socket.recv().decode()
                print("got message to go to port", port)
                break
            except zmq.error.Again:
                continue
        socket.close()
        return self._generateConnectSocket(zmq.PAIR, address, port)

    #############################
    ### ACCEPT NEW CONNECTION ###
    #############################

    def _getUniquePort(self):
        while self.currentPairPort in self.currentlyBoundPorts:
            self.currentPairPort += 1
        return self.currentPairPort

    def _handleConnectionRequests(self, address, request):
        if request != CONN_REQUEST:
            raise RuntimeError('Received a connection request without appropriate metadata')

        portToUse = self._getUniquePort()
        socket = self._generateBindSocket(zmq.PAIR, self.currentPairPort)
        
        uuid = self._generateSocketUUID()
        with self._directConnectionsLock:
            self._directConnections[uuid] = socket
        self.currentlyBoundPorts.append(self.currentPairPort)

        self._routingSocket.send_multipart([
            address,
            b'',
            '{}'.format(self.currentPairPort).encode(),
        ])

    #####################
    ### MAIN RUN LOOP ###
    #####################

    def start(self):
        if self.willPublish:
            self._publisher = self._generateBindSocket(zmq.PUB, self.pubsubPort)
            self.currentPairPort.append(self.pubsubPort)
        else:
            self._publisher = None

        self._routingSocket = self._generateBindSocket(zmq.ROUTER, self.pairRoutingPort)
        self.currentlyBoundPorts.append(self.pairRoutingPort)

        Thread(target=self._run, args=()).start()
        self.started = True
        return self

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

            with self._directConnectionsLock:
                for socket in self._directConnections.values():
                    try:
                        message = socket.recv()
                        self._handleMessage(message)
                    except zmq.error.Again:
                        pass

            for socket in self._subscribers:
                try:
                    message = socket.recv()
                    raise RuntimeError('Not implemented') # TODO: Implement
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

    def _close(self):
        self.started = False
        with self._directConnectionsLock:
            for socket in self._directConnections.values():
                socket.close()
        if self._publisher is not None:
            self._publisher.close()
        for socket in self._subscribers:
            socket.close()
        self.closeEvent.set()

    def close(self):
        self.stopped = True
        self.closeEvent.wait()

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

        with self._directConnectionsLock:
            for socket in self._directConnections.values():
                socket.send(toSend)


    def send(self, topic, data, routingID=None):
        message = SocketMessage()
        message.type = topic
        message.data = data
        self._sendMessage(message, routingID)

    def get(self, topic):
        return self._topics.get(topic, None)

    def publish(self, topic, data):
        if not self.willPublish:
            raise RuntimeError('Unable to publish message; configuration specifies Transport will not publish.')
        message = SocketMessage()
        message.type = topic
        message.data = data
        toSend = message.SerializeToString()
        if self.compression:
            toSend = compress(toSend)

        self._publisher.send(topic.encode() + DELIMITER + toSend)

    def waitForMessageOnTopic(self, topic):
        if self.get(topic) is not None:
            return
        event = Event()
        self._topicEvents[topic] = event
        event.wait()

























    # def receive(self, socketConnection, addr, port):
    #     self.socket = socketConnection
    #     self.addr = addr
    #     self.port = port
    #     self.socket.settimeout(self.timeout)
    #     self.__start()

    # def __start(self):
    #     if self.socket is None:
    #         raise RuntimeError('Connection started without socket')
    #     Thread(target=self.__run, args=()).start()
    #     return self

    # def __run(self):
    #     buff = b''
    #     foundDelimiter = False
    #     self.opened = True
    #     self.openEvent.set()
    #     while True:
    #         if self.stopped:
    #             return

    #         try:
    #             read = self.socket.recv(self.readSize)
    #             if DELIMITER in buff[-DELIMITER_SIZE:] + read:
    #                 foundDelimiter = True
    #             buff += read
    #         except socket.timeout:
    #             continue
    #         except OSError:
    #             self.__close()

    #         if buff != b'' and foundDelimiter:
    #             with self.parseLock:
    #                 buff = self.__processMessage(buff)
    #                 foundDelimiter = False

    #         self.__sendWaitingMessages()

    # def __processMessage(self, buff):
    #     messages = buff.split(DELIMITER)
    #     if self.compress:
    #         for i in range(len(messages)):
    #             try:
    #                 messages[i] = decompress(messages[i])
    #             except zlibError:
    #                 continue

    #     for i in range(len(messages)):
    #         message = SocketMessage()
    #         try:
    #             message.ParseFromString(messages[i])
    #         except protobuf.message.DecodeError:
    #             continue

    #         if message.type == IMAGE:
    #             self._topics[IMAGE] = decodeImg(message.data)
    #         elif message.data != '':
    #             self._topics[message.type] = message.data
            
            
    #         self.__cascade(message)
    #         messages[i] = b''

    #     return b''.join(messages)

    # def __cascade(self, message):
    #     meta = message.meta
    #     if meta == ACK:
    #         self.writeAvailable = True
    #         self.writeAvailableEvent.set()
    #     elif meta == CLOSING:
    #         self.__close()
    #     if message.acknowledge:
    #         self.__ack()

    # def __ack(self):
    #     self.__writeMeta(ACK)

    # def __writeMeta(self, meta, data=None):
    #     message = SocketMessage()
    #     message.meta = meta
    #     if data:
    #         message.data = data
    #     self.__sendAll(message, overrideAck=True)

    # def __sendAll(self, message, overrideAck=False):
    #     if (self.writeAvailable or overrideAck) and self.opened:
    #         with self.writeLock:
    #             if self.acknowledge and not overrideAck:
    #                 message.acknowledge = True

    #             # pylint: disable=singleton-comparison
    #             if message.acknowledge == True:
    #                 self.writeAvailable = False
    #                 self.writeAvailableEvent.clear()

    #             toSend = message.SerializeToString()
    #             if self.compress:
    #                 toSend = compress(toSend)
    #             self.socket.sendall(toSend + DELIMITER)

    #     else:
    #         if not self.bufferEnabled and message.meta != CLOSING:
    #             raise RuntimeError('Unable to write; port locked or not opened')
    #         self.waitingBuffer.append(message)

    # def __close(self):
    #     self.stopped = True
    #     self.socket.close()
    #     self.opened = False
    #     self.closeEvent.set()

    # #################
    # ### INTERFACE ###
    # #################

    # def connect(self, addr, port):
    #     self.addr = addr
    #     self.port = port
    #     while True:
    #         try:
    #             self.socket = generateSocket(self.timeout)
    #             self.socket.connect((self.addr, self.port))
    #             break
    #         except (socket.timeout, socket.gaierror, OSError) as error:
    #             self.socket.close()
    #             if isinstance(error, OSError) and not isinstance(error, ConnectionRefusedError):
    #                 raise RuntimeError('Socket address in use: {}'.format(error))
    #     self.__start()

    # def openForConnection(self, port):
    #     self.port = port
    #     while True:
    #         try:
    #             self.socket = generateSocket(self.timeout)
    #             self.socket.bind(('', self.port))
    #             self.socket.listen()
    #             break
    #         except (socket.timeout, OSError) as error:
    #             self.socket.close()
    #             if isinstance(error, OSError):
    #                 raise RuntimeError('Socket address in use: {}'.format(error))
    #     while True:
    #         try:
    #             conn, addr = self.socket.accept()
    #             addr, port = addr
    #             oldSocket = self.socket
    #             self.receive(conn, addr, port)
    #             oldSocket.close()
    #             break
    #         except (OSError, socket.timeout):
    #             continue

    # def get(self, channel):
    #     with self.parseLock:
    #         return self._topics[channel] if channel in self._topics.keys() else None

    # def getImage(self):
    #     return self._topics[IMAGE] if IMAGE in self._topics.keys() else None

    # def canWrite(self):
    #     return (self.writeAvailable and self.opened and not self.stopped) or self.bufferEnabled

    # def write(self, channel, data, requireAck=False):
    #     message = SocketMessage()
    #     message.type = channel.replace('\n', '')
    #     message.data = data.replace('\n', '')
    #     if requireAck:
    #         message.acknowledge = True
    #     self.__sendAll(message)

    # def writeImage(self, data, requireAck=False):
    #     message = SocketMessage()
    #     message.type = IMAGE
    #     message.data = encodeImg(data)
    #     if requireAck:
    #         message.acknowledge = True
    #     self.__sendAll(message)

    # def close(self):
    #     try:
    #         self.__writeMeta(CLOSING)
    #     except OSError:
    #         pass
    #     self.__close()

    # def registerCallback(self, channel, function):
    #     self._callbacks[channel] = function

    # #############################
    # ### SYNCHRONOUS INTERFACE ###
    # #############################

    # def waitForReady(self):
    #     if self.bufferEnabled:
    #         return True
    #     self.openEvent.wait()
    #     while not self.writeAvailableEvent.isSet():
    #         self.writeAvailableEvent.wait()

    # def waitForClose(self):
    #     return self.closeEvent.wait()

    # def waitForOpen(self):
    #     return self.openEvent.wait()

    # def waitForChannel(self, channel):
    #     if self.get(channel) is not None:
    #         return True
    #     self.channelEvent.clear()
    #     self.channelListener = channel
    #     while not self.channelEvent.isSet():
    #         self.channelEvent.wait()

    # def waitForImage(self):
    #     return self.waitForChannel(IMAGE)

    # def writeSync(self, channel, data):
    #     self.write(channel, data, requireAck=True)
    #     return self.writeAvailableEvent.wait()

    # def writeImageSync(self, data):
    #     self.writeImage(data, requireAck=True)
    #     return self.writeAvailableEvent.wait()
