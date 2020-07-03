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

    def __init__(self, name=None, timeout=TIMEOUT, size=SIZE, compress=False):
        self.name = name
        self.channels = {}
        self.timeout = timeout
        self.size = size
        self.compress = compress
        self.canWrite = True
        self.stopped = False
        self.opened = False
        self.socket = None
        self.addr = None
        self.port = None
        self.type = None
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
                    else:
                        self.channels[msg.type] = msg.data
                    data[i] = b''
                    self.__cascade(msg)

                tmp = b''.join(data)

    def __cascade(self, message):
        meta = message.meta
        if meta == ACK:
            self.canWrite = True
        elif meta == CLOSING:
            self.__close()
        elif meta == NAME_CONN:
            self.name = message.data
        if message.ackRequired:
            self.__ack()

    def __ack(self):
        self.__writeMeta(ACK)

    def __writeMeta(self, meta, data=None):
        msg = SocketMessage()
        msg.meta = meta
        if data:
            msg.data = data
        toSend = msg.SerializeToString() + DELIMITER
        if self.compress:
            toSend = zlib.compress(toSend)
        self.socket.sendall(toSend)

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
            except socket.timeout:
                self.socket.close()
                continue
            except socket.gaierror:
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
            except OSError:
                continue
            except socket.timeout:
                continue

    def get(self, channel):
        with self.lock:
            if channel in self.channels.keys():
                return self.channels[channel]
            return None

    def getImage(self):
        if IMAGE in self.channels.keys():
            return self.channels[IMAGE]
        return None

    def write(self, channel, data):
        if self.canWrite and self.opened:
            with self.lock:
                msg = SocketMessage()
                msg.type = channel.replace('\n', '')
                msg.data = data.replace('\n', '')
                toSend = msg.SerializeToString() + DELIMITER
                if self.compress:
                    toSend = zlib.compress(toSend)
                self.socket.sendall(toSend)

    def writeImage(self, data):
        if self.canWrite and self.opened:
            with self.lock:
                self.canWrite = False
                msg = SocketMessage()
                msg.type = IMAGE
                msg.data = encodeImg(data)
                msg.ackRequired = True
                self.socket.sendall(msg.SerializeToString() + DELIMITER)

    def close(self):
        try:
            self.__writeMeta(CLOSING)
        except OSError:
            pass
        self.__close()
