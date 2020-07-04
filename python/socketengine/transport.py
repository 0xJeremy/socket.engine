import socket
import zlib
from threading import Thread, Lock
from google import protobuf
from .common import encodeImg, decodeImg, generateSocket
from .message_pb2 import SocketMessage

#################
### CONSTANTS ###
#################

from .constants import ACK, IMAGE, TIMEOUT, SIZE
from .constants import CLOSING, NAME_CONN

DELIMITER = b'xxxxxx'

###############################################################

#######################
### TRANSPORT CLASS ###
#######################

# pylint: disable=invalid-name, consider-using-enumerate, no-member
class Transport:
    TYPE_LOCAL = 1
    TYPE_REMOTE = 2

    def __init__(self, name=None, timeout=TIMEOUT, size=SIZE, compress=False, requireAck=False, enableBuffer=True):
        self.name = name
        self.channels = {}
        self.timeout = timeout
        self.size = size
        self.compress = compress
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
        self.lock = Lock()

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
        while True:
            if self.stopped:
                self.socket.close()
                return

            try:
                tmp += self.socket.recv(self.size)
            except socket.timeout:
                continue
            except OSError:
                self.close()

            if tmp != b'':
                tmp = self.__processMessage(tmp)

            self.__sendWaitingMessages()

    def __sendWaitingMessages(self):
        # pylint: disable=unused-variable
        for i in range(len(self.waitingBuffer)):
            message = self.waitingBuffer.pop(0)
            self.__sendAll(message)

    def __processMessage(self, tmp):
        if self.compress:
            try:
                data = zlib.decompress(tmp).split(DELIMITER)
            except zlib.error:
                data = tmp.split(DELIMITER)
        else:
            data = tmp.split(DELIMITER)

        for i in range(len(data)):
            msg = SocketMessage()
            try:
                msg.ParseFromString(data[i])
            except protobuf.message.DecodeError:
                continue

            if msg.type == IMAGE:
                self.channels[IMAGE] = decodeImg(msg.data)
            elif msg.data != b'' and msg.data != '':
                self.channels[msg.type] = msg.data
            self.__cascade(msg)
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

    def __writeMeta(self, meta, data=None, overrideAck=True):
        msg = SocketMessage()
        msg.meta = meta
        if data:
            msg.data = data
        self.__sendAll(msg, overrideAck)

    def __sendAll(self, message, overrideAck=False):
        if (not self.writeAvailable or not self.opened) and not overrideAck:
            if self.enableBuffer:
                self.waitingBuffer.append(message)
            else:
                raise RuntimeError('Unable to write; port locked or not opened')

        with self.lock:
            if self.ackRequired and not overrideAck:
                self.writeAvailable = False
                message.ackRequired = True

            toSend = message.SerializeToString() + DELIMITER
            if self.compress:
                toSend = zlib.compress(toSend)

            try:
                self.socket.sendall(toSend)
            except (ConnectionResetError, BrokenPipeError) as error:
                if self.enableBuffer:
                    self.waitingBuffer.append(message)
                else:
                    raise error

    def __close(self):
        self.opened = False
        self.stopped = True

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
        with self.lock:
            return self.channels[channel] if channel in self.channels.keys() else None

    def getImage(self):
        return self.channels[IMAGE] if IMAGE in self.channels.keys() else None

    def canWrite(self):
        if self.enableBuffer:
            return True
        return self.writeAvailable and self.opened and not self.stopped

    def write(self, channel, data):
        msg = SocketMessage()
        msg.type = channel.replace('\n', '')
        msg.data = data.replace('\n', '')
        self.__sendAll(msg)

    def writeImage(self, data):
        msg = SocketMessage()
        msg.type = IMAGE
        msg.data = encodeImg(data)
        self.__sendAll(msg)

    def close(self):
        try:
            self.__writeMeta(CLOSING)
        except OSError:
            pass
        self.__close()
