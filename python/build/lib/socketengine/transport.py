import socket
from threading import Thread, Lock
from json import dumps as dictToJson
from json import loads as jsonToDict
from json.decoder import JSONDecodeError
from .common import encodeImg, decodeImg, generateSocket

#################
### CONSTANTS ###
#################

from .constants import ACK, NEWLINE, IMG_MSG_S, IMG_MSG_E
from .constants import IMAGE, TYPE, DATA
from .constants import PORT, TIMEOUT, SIZE
from .constants import STATUS, CLOSING, NAME_CONN
from .constants import MAX_RETRIES

###############################################################

#######################
### TRANSPORT CLASS ###
#######################


class Transport:
    TYPE_LOCAL = 1
    TYPE_REMOTE = 2

    def __init__(self, name, timeout=TIMEOUT, size=SIZE):
        self.name = name
        self.socket = None
        self.addr, self.port = None, None
        self.canWrite = True
        self.channels = {}
        self.timeout = timeout
        self.size = size
        self.stopped = False
        self.opened = False
        self.type = None
        self.lock = Lock()

    def receive(self, socket, addr, port):
        self.socket = socket
        self.addr = addr
        self.port = port
        self.socket.settimeout(self.timeout)
        self.type = Transport.TYPE_REMOTE
        self.opened = True
        self.__start()

    def __start(self):
        if self.socket is None:
            raise RuntimeError("Connection started without socket")
            return
        Thread(target=self.__run, args=()).start()
        return self

    def __run(self):
        tmp = ""
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

            if tmp != "":
                data = tmp.split("\n")
                for i in range(len(data)):
                    try:
                        msg = jsonToDict(data[i])
                    except JSONDecodeError:
                        continue

                    self.__cascade(msg[TYPE], msg[DATA])
                    if msg[TYPE] == IMAGE:
                        self.channels[IMAGE] = decodeImg(msg[DATA])
                    else:
                        self.channels[msg[TYPE]] = msg[DATA]
                    data[i] = ""

                tmp = "".join(data)

    def __cascade(self, mtype, mdata):
        if mtype == ACK:
            self.canWrite = True
        if mtype == STATUS:
            if mdata == CLOSING:
                self.__close()
        if mtype == NAME_CONN:
            self.name = mdata
        if mtype == IMAGE:
            self.write(ACK, ACK)

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
                continue
            except socket.gaierror:
                continue
            except OSError as e:
                if type(e) == ConnectionRefusedError:
                    continue
                raise RuntimeError("Socket address in use: {}".format(e))
                return
        self.type = Transport.TYPE_LOCAL
        self.opened = True
        self.write(NAME_CONN, self.name)
        self.__start()

    def get(self, channel):
        with self.lock:
            if channel in self.channels.keys():
                return self.channels[channel]
            return None

    def getImg(self):
        if IMAGE in self.channels.keys():
            return self.channels[IMAGE]
        return None

    def write(self, channel, data):
        if self.opened:
            with self.lock:
                msg = {TYPE: channel.replace("\n", ""), DATA: data.replace("\n", "")}
                self.socket.sendall(dictToJson(msg).encode() + NEWLINE)

    def writeImg(self, data):
        if self.canWrite and self.opened:
            with self.lock:
                self.canWrite = False
                self.socket.sendall(IMG_MSG_S + encodeImg(data) + IMG_MSG_E + NEWLINE)

    def close(self):
        try:
            self.write(STATUS, CLOSING)
        except OSError:
            pass
        self.__close()
