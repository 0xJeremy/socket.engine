import socket
from threading import Thread, Event
from .engine_commons import generateSocket
from .transport import Transport

#################
### CONSTANTS ###
#################

from .constants import PORT, TIMEOUT, SIZE

###############################################################

#################
### HUB CLASS ###
#################

# pylint: disable=invalid-name, unused-variable
class Router:
    # fmt:off
    def __init__(
            self,
            port=PORT,
            timeout=TIMEOUT,
            readSize=SIZE,
            useCompression=False,
            requireAck=False,
            bufferEnabled=False,
            findOpenPort=False,
    ):
    # fmt:on
        self.socket = None
        self.port = port
        self.timeout = timeout
        self.readSize = readSize
        self.useCompression = useCompression
        self.requireAck = requireAck
        self.bufferEnabled = bufferEnabled
        self.findOpenPort = findOpenPort
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
            except (OSError, socket.timeout) as error:
                self.socket.close()
                if isinstance(error, OSError):
                    if not self.findOpenPort:
                        raise RuntimeError('Socket address in use: {}'.format(error))
                    self.port += 1

    def __start(self):
        if self.socket is None:
            raise RuntimeError('Router started without host socket')
        Thread(target=self.__run, args=()).start()
        return self

    def __run(self):
        self.opened = True
        while not self.stopped:
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
        transport = Transport(
            timeout=self.timeout,
            readSize=self.readSize,
            useCompression=self.useCompression,
            requireAck=self.requireAck,
            bufferEnabled=self.bufferEnabled,
        )
        if localInitiation:
            transport.connect(addr, port)
            transport.assignName(name)
        else:
            transport.receive(connection, addr, port)
        self.transports.append(transport)
        self.transportEvent.set()

    #################
    ### INTERFACE ###
    #################

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

    def getImageAll(self):
        data = []
        for transport in self.transports:
            tmp = transport.getImage()
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

    def writeImageAll(self, data):
        for transport in self.transports:
            transport.writeImg(data)
        return self

    def writeImageToName(self, name, data):
        for transport in self.transports:
            if transport.name == name:
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
