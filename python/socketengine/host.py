import socket
from threading import Thread, Lock
from json import dumps as dictToJson
from json import loads as jsonToDict
from json.decoder import JSONDecodeError
from .common import encodeImg, generateSocket

#################
### CONSTANTS ###
#################

from .constants import ACK, NEWLINE, IMG_MSG_S, IMG_MSG_E
from .constants import ADDR, PORT, TIMEOUT, SIZE, OPEN

########################
### CONNECTION CLASS ###
########################

# pylint: disable=consider-using-enumerate
class _connection:
    def __init__(self, socketConnection, address, timeout, size):
        self.socket = socketConnection
        self.address = address
        self.canWrite = True
        self.channels = {}
        self.timeout = timeout
        self.socket.settimeout(self.timeout)
        self.size = size
        self.stopped = False
        self.lock = Lock()
        self.start()

    def start(self):
        Thread(target=self.run, args=()).start()
        return self

    def run(self):
        tmp = ''
        while True:
            if self.stopped:
                self.socket.close()
                return

            try:
                tmp += self.socket.recv(self.size).decode()
            except socket.timeout:
                continue
            except OSError:
                self.close()

            if tmp not in ('', '\n'):
                data = tmp.split('\n')
                for i in range(len(data)):
                    try:
                        msg = jsonToDict(data[i])
                        self.channels[msg['type']] = msg['data']
                        if msg['type'] == ACK:
                            self.canWrite = True
                        tmp = ''
                    except JSONDecodeError:
                        tmp = ''.join(data[i:])
                        break

    def get(self, channel):
        with self.lock:
            if channel in self.channels.keys():
                return self.channels[channel]
            return None

    def writeLock(self, channel, data):
        with self.lock:
            self.write(channel, data)

    def write(self, channel, data):
        msg = {'type': channel, 'data': data}
        self.socket.sendall(dictToJson(msg).encode() + NEWLINE)

    def writeImgLock(self, data):
        with self.lock:
            self.writeImg(data)

    def writeImg(self, data):
        if self.canWrite:
            self.canWrite = False
            msg = IMG_MSG_S + encodeImg(data) + IMG_MSG_E
            self.socket.sendall(msg + NEWLINE)

    def close(self):
        self.stopped = True


##################
### HOST CLASS ###
##################

# pylint: disable=redefined-builtin, unused-variable
class Host:
    def __init__(self, addr=ADDR, port=PORT, timeout=TIMEOUT, size=SIZE, open=OPEN):
        self.addr = addr
        self.port = port
        self.timeout = timeout
        self.size = size
        self.connections = []
        self.clients = []
        self.stopped = False
        self.opened = False
        if open:
            self.open()

    def setTimeout(self, time):
        self.timeout = time

    def open(self):
        while True:
            try:
                self.socket = generateSocket(self.timeout)
                self.socket.bind(('', self.port))
                self.socket.listen()
                break
            except OSError as error:
                raise RuntimeError('Socket address in use: {}'.format(error))
            except socket.timeout:
                continue
        self.opened = True

    def start(self):
        Thread(target=self.run, args=()).start()
        return self

    def run(self):
        tmp = ''
        while True:
            if self.stopped:
                for client in self.clients:
                    client.close()
                self.socket.close()
                return

            try:
                conn, addr = self.socket.accept()
                if addr not in self.connections:
                    self.connections.append(addr)
                    self.clients.append(_connection(conn, addr, self.timeout, self.size))
            except socket.timeout:
                continue

    def getAll(self, channel):
        data = []
        for client in self.clients:
            tmp = client.get(channel)
            if tmp is not None:
                data.append(tmp)
        return data

    def getClients(self):
        return self.clients

    def writeAllLock(self, channel, data):
        for client in self.clients:
            client.writeLock(channel, data)
        return self

    def writeAll(self, channel, data):
        for client in self.clients:
            client.write(channel, data)
        return self

    def writeImageLockAll(self, data):
        for client in self.clients:
            client.writeImg(data)
        return self

    def writeImageAll(self, data):
        for client in self.clients:
            client.writeImg(data)
        return self

    def close(self):
        self.opened = False
        for client in self.clients:
            client.close()
        self.stopped = True
