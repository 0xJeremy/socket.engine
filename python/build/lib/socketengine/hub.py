import socket
from threading import Thread, Lock
from .common import generateSocket
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
        self.__open()
        self.__start()

    def __open(self):
        while True:
            try:
                self.socket = generateSocket(self.timeout)
                self.socket.bind(("", self.port))
                self.socket.listen()
                break
            except OSError as e:
                if self.userDefinedPort or self.port > (PORT + MAX_RETRIES):
                    raise RuntimeError("Socket address in use: {}".format(e))
                    return
                self.port += 1
            except socket.timeout:
                continue

    def __start(self):
        if self.socket is None:
            raise RuntimeError("Hub started without host socket")
        self.opened = True
        Thread(target=self.__run, args=()).start()
        return self

    def __run(self):
        tmp = ""
        while True:
            if self.stopped:
                for t in self.transports:
                    t.close()
                self.socket.close()
                return

            try:
                s, addr = self.socket.accept()
                if addr not in self.transportAddresses:
                    self.transportAddresses.append(addr)
                    addr, port = addr
                    t = Transport(None, self.timeout, self.size)
                    t.receive(s, addr, port)
                    self.transports.append(t)
            except socket.timeout:
                continue

    def connect(self, name, addr, port):
        t = Transport(self.timeout, self.size)
        t.connect(name, addr, port)
        self.transports.append(t)
        return self

    def close(self):
        self.opened = False
        self.stopped = True

    def getConnections(self):
        return self.transports

    ##########################
    ### INTERFACE, GETTERS ###
    ##########################

    def get_all(self, channel):
        data = []
        for t in self.transports:
            tmp = t.get(channel)
            if tmp is not None:
                data.append(tmp)
        return data

    def get_by_name(self, name, channel):
        data = []
        for t in self.transports:
            if t.name == name:
                tmp = t.get(channel)
                if tmp is not None:
                    data.append(tmp)
        return data

    def get_local(self, channel):
        data = []
        for t in self.transports:
            if t.type == transport.TYPE_LOCAL:
                tmp = t.get(channel)
                if tmp is not None:
                    data.append(tmp)
        return data

    def get_remote(self, channel):
        data = []
        for t in self.transports:
            if t.type == transport.TYPE_REMOTE:
                tmp = t.get(channel)
                if tmp is not None:
                    data.append(tmp)
        return data

    ##########################
    ### INTERFACE, WRITERS ###
    ##########################

    def write_all(self, channel, data):
        for t in self.transports:
            t.write(channel, data)
        return self

    def write_to_name(self, name, channel, data):
        for t in self.transports:
            if t.name == name:
                t.write(channel, data)
        return self

    def write_to_local(self, channel, data):
        for t in self.transports:
            if t.type == transport.TYPE_REMOTE:
                t.write(channel, data)
        return self

    def write_to_remote(self, channel, data):
        for t in self.transports:
            if t.type == transport.TYPE_LOCAL:
                t.write(channel, data)
        return self

    def write_image_all(self, data):
        for t in self.transports:
            t.writeImg(data)
        return self

    def write_image_to_name(self, name, data):
        for t in self.transports:
            if t.name == name:
                t.writeImg(data)
        return self

    def write_image_to_local(self, data):
        for t in self.transports:
            if t.type == transport.TYPE_REMOTE:
                t.writeImg(data)
        return self

    def write_image_to_remote(self, data):
        for t in self.transports:
            if t.type == transport.TYPE_LOCAL:
                t.writeImg(data)
        return self
