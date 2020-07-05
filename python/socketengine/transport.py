import socket
from threading import Thread, Lock, Event
from zlib import compress, decompress
from zlib import error as zlibError
from google import protobuf
from .engine_commons import encodeImg, decodeImg, generateSocket
from .message_pb2 import SocketMessage

#################
### CONSTANTS ###
#################

from .constants import ACK, IMAGE, TIMEOUT, SIZE
from .constants import CLOSING, NAME_CONN

DELIMITER = b'\0\0\0'
DELIMITER_SIZE = len(DELIMITER)

###############################################################

#######################
### TRANSPORT CLASS ###
#######################

# pylint: disable=invalid-name, consider-using-enumerate, no-member, too-many-instance-attributes
class Transport:
    TYPE_LOCAL = 1
    TYPE_REMOTE = 2

    # fmt: off
    def __init__(
            self, name=None, timeout=TIMEOUT, size=SIZE, useCompression=False, requireAck=False, enableBuffer=False
    ):
    # fmt: on
        self.name = name
        self.channels = {}
        self.timeout = timeout
        self.size = size
        self.compress = useCompression
        self.writeAvailable = True
        self.stopped = False
        self.opened = False
        self.socket = None
        self.addr = None
        self.port = None
        self.type = None
        self.ackRequired = requireAck
        self.enableBuffer = enableBuffer
        self.waitingBuffer = []
        self.parseLock = Lock()
        self.writeLock = Lock()
        self.closeEvent = Event()
        self.openEvent = Event()
        self.nameEvent = Event()
        self.writeAvailableEvent = Event()
        self.writeAvailableEvent.set()
        self.channelListener = None
        self.channelEvent = Event()

    def receive(self, socketConnection, addr, port):
        self.socket = socketConnection
        self.addr = addr
        self.port = port
        self.socket.settimeout(self.timeout)
        self.type = Transport.TYPE_REMOTE
        self.__start()

    def __start(self):
        if self.socket is None:
            raise RuntimeError('Connection started without socket')
        Thread(target=self.__run, args=()).start()
        return self

    def __run(self):
        buff = b''
        foundDelimiter = False
        self.opened = True
        self.openEvent.set()
        while True:
            if self.stopped:
                return

            try:
                read = self.socket.recv(self.size)
                if DELIMITER in buff[-DELIMITER_SIZE:] + read:
                    foundDelimiter = True
                buff += read
            except socket.timeout:
                continue
            except OSError:
                self.__close()

            if buff != b'' and foundDelimiter:
                with self.parseLock:
                    buff = self.__processMessage(buff)
                    foundDelimiter = False

            self.__sendWaitingMessages()

    def __sendWaitingMessages(self):
        # pylint: disable=unused-variable
        for i in range(len(self.waitingBuffer)):
            message = self.waitingBuffer.pop(0)
            self.__sendAll(message)

    def __processMessage(self, buff):
        messages = buff.split(DELIMITER)
        if self.compress:
            for i in range(len(messages)):
                try:
                    messages[i] = decompress(messages[i])
                except zlibError:
                    continue

        for i in range(len(messages)):
            message = SocketMessage()
            try:
                message.ParseFromString(messages[i])
            except protobuf.message.DecodeError:
                continue

            if message.type == IMAGE:
                self.channels[IMAGE] = decodeImg(message.data)
            elif message.data != '':
                self.channels[message.type] = message.data
            if message.type == self.channelListener:
                self.channelEvent.set()
            self.__cascade(message)
            messages[i] = b''

        return b''.join(messages)

    def __cascade(self, message):
        meta = message.meta
        if meta == ACK:
            self.writeAvailable = True
            self.writeAvailableEvent.set()
        elif meta == CLOSING:
            self.__close()
        elif meta == NAME_CONN:
            self.name = message.data
            self.nameEvent.set()
        if message.ackRequired:
            self.__ack()

    def __ack(self):
        self.__writeMeta(ACK)

    def __writeMeta(self, meta, data=None):
        message = SocketMessage()
        message.meta = meta
        if data:
            message.data = data
        self.__sendAll(message, overrideAck=True)

    def __sendAll(self, message, overrideAck=False):
        if (self.writeAvailable or overrideAck) and self.opened:
            with self.writeLock:
                if self.ackRequired and not overrideAck:
                    message.ackRequired = True

                # pylint: disable=singleton-comparison
                if message.ackRequired == True:
                    self.writeAvailable = False
                    self.writeAvailableEvent.clear()

                toSend = message.SerializeToString()
                if self.compress:
                    toSend = compress(toSend)
                self.socket.sendall(toSend + DELIMITER)

        else:
            if not self.enableBuffer and message.meta != CLOSING:
                raise RuntimeError('Unable to write; port locked or not opened')
            self.waitingBuffer.append(message)

    def __close(self):
        self.stopped = True
        self.socket.close()
        self.opened = False
        self.closeEvent.set()

    #################
    ### INTERFACE ###
    #################

    def connect(self, addr, port):
        self.addr = addr
        self.port = port
        while True:
            try:
                self.socket = generateSocket(self.timeout)
                self.socket.connect((self.addr, self.port))
                break
            except (socket.timeout, socket.gaierror, OSError) as error:
                self.socket.close()
                if isinstance(error, OSError) and not isinstance(error, ConnectionRefusedError):
                    raise RuntimeError('Socket address in use: {}'.format(error))
        self.type = Transport.TYPE_LOCAL
        self.__start()

    def openForConnection(self, port):
        self.port = port
        while True:
            try:
                self.socket = generateSocket(self.timeout)
                self.socket.bind(('', self.port))
                self.socket.listen()
                break
            except (socket.timeout, OSError) as error:
                self.socket.close()
                if isinstance(error, OSError):
                    raise RuntimeError('Socket address in use: {}'.format(error))
        while True:
            try:
                conn, addr = self.socket.accept()
                addr, port = addr
                oldSocket = self.socket
                self.receive(conn, addr, port)
                oldSocket.close()
                break
            except (OSError, socket.timeout):
                continue

    def assignName(self, name):
        self.name = name
        self.__writeMeta(NAME_CONN, self.name)

    def get(self, channel):
        with self.parseLock:
            return self.channels[channel] if channel in self.channels.keys() else None

    def getImage(self):
        return self.channels[IMAGE] if IMAGE in self.channels.keys() else None

    def canWrite(self):
        return (self.writeAvailable and self.opened and not self.stopped) or self.enableBuffer

    def waitForReady(self):
        if self.enableBuffer:
            return True
        self.openEvent.wait()
        return self.writeAvailableEvent.wait()

    def write(self, channel, data, requireAck=False):
        message = SocketMessage()
        message.type = channel.replace('\n', '')
        message.data = data.replace('\n', '')
        if requireAck:
            message.ackRequired = True
        self.__sendAll(message)

    def writeImage(self, data, requireAck=False):
        message = SocketMessage()
        message.type = IMAGE
        message.data = encodeImg(data)
        if requireAck:
            message.ackRequired = True
        self.__sendAll(message)

    def close(self):
        try:
            self.__writeMeta(CLOSING)
        except OSError:
            pass
        self.__close()

    #############################
    ### SYNCHRONOUS INTERFACE ###
    #############################

    def waitForClose(self):
        return self.closeEvent.wait()

    def waitForOpen(self):
        return self.openEvent.wait()

    def waitForName(self):
        return self.nameEvent.wait()

    def waitForChannel(self, channel):
        if self.get(channel) is not None:
            return True
        self.channelEvent.clear()
        self.channelListener = channel
        while not self.channelEvent.isSet():
            self.channelEvent.wait()

    def waitForImage(self):
        return self.waitForChannel(IMAGE)

    def writeImageSync(self, data):
        self.writeImage(data, requireAck=True)
        return self.writeAvailableEvent.wait()

    def writeSync(self, channel, data):
        self.write(channel, data, requireAck=True)
        return self.writeAvailableEvent.wait()
