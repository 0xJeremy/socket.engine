import socket
from threading import Thread, Event
from .engine_commons import generateSocket
from .transport import Transport

#################
### CONSTANTS ###
#################

from .constants import PORT, TIMEOUT, SIZE
from .constants import MAX_RETRIES

###############################################################

#################
### HUB CLASS ###
#################

# pylint: disable=unused-variable, invalid-name, too-many-public-methods
class Hub:
    def __init__(self, port=None, timeout=TIMEOUT, size=SIZE):
        self.socket = None
        self.userDefinedPort = port is not None
        self.port = port or PORT
        self.timeout = timeout
        self.size = size
        self.transports = []
        self.transportAddresses = []
        self.stopped = False
        self.opened = False
        self.transportEvent = Event()
        self.__open()
        self.__start()

    def __open(self):
        while True:
            try:
                self.socket = generateSocket(self.timeout)
                self.socket.bind(('', self.port))
                self.socket.listen()
                return
            except OSError as error:
                self.socket.close()
                if self.userDefinedPort or self.port > (PORT + MAX_RETRIES):
                    raise RuntimeError('Socket address in use: {}'.format(error))
                self.port += 1
            except socket.timeout:
                self.socket.close()
                continue

    def __start(self):
        if self.socket is None:
            raise RuntimeError('Hub started without host socket')
        self.opened = True
        Thread(target=self.__run, args=()).start()
        return self

    def __run(self):
        while True:
            if self.stopped:
                return

            try:
                conn, addr = self.socket.accept()
                if addr not in self.transportAddresses:
                    self.transportAddresses.append(addr)
                    addr, port = addr
                    self.__addTransport(addr, port, False, connection=conn)
            except socket.timeout:
                continue
            except OSError:
                self.close()

    def __addTransport(self, addr, port, localInitiation, name=None, connection=None):
        self.transportEvent.clear()
        transport = Transport(timeout=self.timeout, size=self.size)
        if localInitiation:
            transport.connect(addr, port)
            transport.assignName(name)
        else:
            transport.receive(connection, addr, port)
        self.transports.append(transport)
        self.transportEvent.set()

    def connect(self, name, addr, port):
        self.__addTransport(addr, port, True, name=name)
        return self

    def close(self):
        self.stopped = True
        for transport in self.transports:
            transport.close()
        self.socket.close()
        self.opened = False

    def getConnections(self):
        return self.transports

    def waitForTransport(self):
        return self.transportEvent.wait()

    ##########################
    ### INTERFACE, GETTERS ###
    ##########################

    def canWriteAll(self):
        return all([transport.canWrite() for transport in self.transports])

    def getAll(self, channel):
        data = []
        for transport in self.transports:
            tmp = transport.get(channel)
            if tmp is not None:
                data.append(tmp)
        return data

    def getByName(self, name, channel):
        data = []
        for transport in self.transports:
            if transport.name == name:
                tmp = transport.get(channel)
                if tmp is not None:
                    data.append(tmp)
        return data

    def getLocal(self, channel):
        data = []
        for transport in self.transports:
            if transport.type == transport.TYPE_LOCAL:
                tmp = transport.get(channel)
                if tmp is not None:
                    data.append(tmp)
        return data

    def getRemote(self, channel):
        data = []
        for transport in self.transports:
            if transport.type == transport.TYPE_REMOTE:
                tmp = transport.get(channel)
                if tmp is not None:
                    data.append(tmp)
        return data

    ##########################
    ### INTERFACE, WRITERS ###
    ##########################

    def writeAll(self, channel, data):
        for transport in self.transports:
            transport.write(channel, data)
        return self

    def writeToName(self, name, channel, data):
        for transport in self.transports:
            if transport.name == name:
                transport.write(channel, data)
        return self

    def writeToLocal(self, channel, data):
        for transport in self.transports:
            if transport.type == transport.TYPE_REMOTE:
                transport.write(channel, data)
        return self

    def writeToRemote(self, channel, data):
        for transport in self.transports:
            if transport.type == transport.TYPE_LOCAL:
                transport.write(channel, data)
        return self

    def writeImageAll(self, data):
        for transport in self.transports:
            transport.writeImg(data)
        return self

    def writeImageToName(self, name, data):
        for transport in self.transports:
            if transport.name == name:
                transport.writeImg(data)
        return self

    def writeImageToLocal(self, data):
        for transport in self.transports:
            if transport.type == transport.TYPE_REMOTE:
                transport.writeImg(data)
        return self

    def writeImageToRemote(self, data):
        for transport in self.transports:
            if transport.type == transport.TYPE_LOCAL:
                transport.writeImg(data)
        return self

    #############################
    ### SYNCHRONOUS INTERFACE ###
    #############################

    def writeAllWhenReady(self, channel, data):
        for transport in self.transports:
            transport.waitForReady()
        self.writeAll(channel, data)

    def writeToNameWhenReady(self, name, channel, data):
        for transport in self.transports:
            if transport.name == name:
                transport.waitForReady()
        self.writeToName(name, channel, data)

    def waitForGetAll(self, channel):
        for transport in self.transports:
            transport.waitForChannel(channel)
        return self.getAll(channel)

    def waitForAllReady(self):
        for transport in self.transports:
            transport.waitForReady()
