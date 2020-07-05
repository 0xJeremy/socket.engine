import socket
import time
from threading import Thread, Lock
from zlib import compress, decompress
from zlib import error as zlibError
from google import protobuf
from .common import encodeImg, decodeImg, generateSocket
from .message_pb2 import SocketMessage

#################
### CONSTANTS ###
#################

from .constants import ACK, IMAGE, TIMEOUT, SIZE
from .constants import CLOSING, NAME_CONN

DELIMITER = b'\0\0\0'
WAIT_TIMEOUT = 10

###############################################################

#######################
### TRANSPORT CLASS ###
#######################

# pylint: disable=invalid-name, consider-using-enumerate, no-member
class Transport:
    TYPE_LOCAL = 1
    TYPE_REMOTE = 2

    def __init__(self, name=None, timeout=TIMEOUT, size=SIZE, useCompression=False, requireAck=False, enableBuffer=False):
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

    def receive(self, socketConnection, addr, port):
        self.socket = socketConnection
        self.addr = addr
        self.port = port
        self.socket.settimeout(self.timeout)
        self.type = Transport.TYPE_REMOTE
        self.opened = True
        self.__start()

    def __start(self):
        if self.socket is None:
            raise RuntimeError('Connection started without socket')
        Thread(target=self.__run, args=()).start()
        return self

    def __run(self):
        tmp = b''
        foundDelimiter = False
        while True:
            if self.stopped:
                return

            try:
                read = self.socket.recv(self.size)
                if DELIMITER in tmp[-3:] + read:
                    foundDelimiter = True
                tmp += read
            except socket.timeout:
                continue
            except OSError:
                self.__close()

            if tmp != b'' and foundDelimiter:
                with self.parseLock:
                    tmp = self.__processMessage(tmp)
                    foundDelimiter = False

            self.__sendWaitingMessages()

    def __sendWaitingMessages(self):
        # pylint: disable=unused-variable
        for i in range(len(self.waitingBuffer)):
            message = self.waitingBuffer.pop(0)
            self.__sendAll(message)

    def __processMessage(self, tmp):
        data = tmp.split(DELIMITER)
        if self.compress:
            for i in range(len(data)):
                try:
                    data[i] = decompress(data[i])
                except zlibError:
                    continue

        for i in range(len(data)):
            message = SocketMessage()
            try:
                message.ParseFromString(data[i])
            except protobuf.message.DecodeError:
                continue

            if message.type == IMAGE:
                self.channels[IMAGE] = decodeImg(message.data)
            elif message.data != '':
                self.channels[message.type] = message.data
            self.__cascade(message)
            data[i] = b''

        return b''.join(data)

    def __cascade(self, message):
        meta = message.meta
        if meta == ACK:
            self.writeAvailable = True
        elif meta == CLOSING:
            self.__close()
        elif meta == NAME_CONN:
            self.name = message.data
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

    #################
    ### INTERFACE ###
    #################

    def connect(self, name, addr, port):
        self.name = name
        self.addr = addr
        self.port = port
        while True:
            try:
                self.socket = generateSocket(self.timeout)
                self.socket.connect((self.addr, self.port))
                break
            except (socket.timeout, socket.gaierror):
                self.socket.close()
                continue
            except OSError as error:
                self.socket.close()
                if isinstance(error, ConnectionRefusedError):
                    continue
                raise RuntimeError('Socket address in use: {}'.format(error))
        self.type = Transport.TYPE_LOCAL
        self.opened = True
        self.__writeMeta(NAME_CONN, self.name)
        self.__start()

    def waitForConnection(self, port):
        self.port = port
        while True:
            try:
                self.socket = generateSocket(self.timeout)
                self.socket.bind(('', self.port))
                self.socket.listen()
                break
            except OSError as error:
                self.socket.close()
                raise RuntimeError('Socket address in use: {}'.format(error))
            except socket.timeout:
                self.socket.close()
                continue
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

    def get(self, channel):
        with self.parseLock:
            return self.channels[channel] if channel in self.channels.keys() else None

    def getImage(self):
        return self.channels[IMAGE] if IMAGE in self.channels.keys() else None

    def canWrite(self):
        return (self.writeAvailable and self.opened and not self.stopped) or self.enableBuffer

    def write(self, channel, data, requireAck=False):
        message = SocketMessage()
        message.type = channel.replace('\n', '')
        message.data = data.replace('\n', '')
        if requireAck:
            message.ackRequired = True
        self.__sendAll(message)

    # Experimental function. Use carefully
    def writeSync(self, channel, data):
        self.write(channel, data, requireAck=True)
        start = time.time()
        while not self.writeAvailable:
            if time.time() - start > WAIT_TIMEOUT:
                raise RuntimeError('Maximum timeout exceeded waiting for acknowledgement')
            time.sleep(0.01)

    def writeImage(self, data, requireAck=False):
        message = SocketMessage()
        message.type = IMAGE
        message.data = encodeImg(data)
        if requireAck:
            message.ackRequired = True
        self.__sendAll(message)

    # Experimental function. Use carefully
    def writeImageSync(self, data):
        self.writeImage(data, requireAck=True)
        start = time.time()
        while not self.writeAvailable:
            if time.time() - start > WAIT_TIMEOUT:
                raise RuntimeError('Maximum timeout exceeded waiting for acknowledgement')
            time.sleep(0.01)

    def close(self):
        try:
            self.__writeMeta(CLOSING)
        except OSError:
            pass
        self.__close()
