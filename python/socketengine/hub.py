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
from .constants import ADDR, PORT, TIMEOUT, SIZE
from .constants import STATUS, CLOSING

########################
### CONNECTION CLASS ###
########################

class connection:
	TYPE_LOCAL = 1
	TYPE_REMOTE = 2

	def __init__(self, timeout=TIMEOUT, size=SIZE):
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

	def __receive(self, socket, addr, port):
		self.socket = socket
		self.addr = addr
		self.port = port
		self.socket.settimeout(self.timeout)
		self.type = connection.TYPE_REMOTE
		self.__start()

	def __start(self):
		if self.socket is None:
			raise RuntimeError("Connection started without socket")
			return
		self.opened = True
		Thread(target=self.__run, args=()).start()
		return self

	def __run(self):
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

			if tmp != '':
				data = tmp.split(NEWLINE)
				for i in range(len(data)):
					try:
						msg = jsonToDict(data[i])
					except: JSONDecodeError:
						continue

					if msg['type'] == STATUS:
						self.__cascade(msg['data'])
					self.channels[msg['type']] = msg['data']
					data[i] = ''

				tmp = ''.join(data)

	def __cascade(self, mdata):
		if mdata == ACK:
			self.canWrite = True
		if mdata == CLOSING:
			self.__close()

	def __close(self):
		self.opened = False
		self.stopped = True

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
			except OSError as e:
				if type(e) == ConnectionRefusedError:
					continue
				raise RuntimeError("Socket address in use: {}".format(e))
				return
			except socket.timeout:
				continue
		self.type = connection.TYPE_LOCAL
		self.__start()

	def get(self, channel):
		with self.lock:
			if channel in self.channels.keys():
				return self.channels[channel]
			return None

	def write(self, channel, data):
		if self.opened:
			with self.lock:
				msg = {
					'type': channel.replace(NEWLINE, ''),
					'data': data.replace(NEWLINE, '')
				}
				self.socket.sendall(dictToJson(msg).encode() + NEWLINE)

	def writeImg(self, image):
		if self.canWrite and self.opened:
			with self.lock:
				self.canWrite = False
				self.socket.sendall(IMG_MSG_S + encodeImg(data) + IMG_MSG_E + NEWLINE)

	def close(self):
		self.write(STATUS, CLOSING)
		self.__close()

	

#################
### HUB CLASS ###
#################

class hub:
	def __init__(self, name=DEFAULT_NAME, port=PORT, timeout=TIMEOUT, size=SIZE):
		self.name = name
		self.port = port
		self.timeout = timeout
		self.size = size
		self.connections = []
		self.address_connections = []
		self.stopped = False
		self.opened = False
		self.__open()
		self.__start()

	def __open(self):
		while True:
			try:
				self.socket = generateSocket(self.timeout)
				self.socket.bind(('', self.port))
				self.socket.listen()
				break
			except OSError as e:
				raise RuntimeError("Socket address in use: {}".format(e))
				return
			except socket.timeout:
				continue

	def __start(self):
		if not self.opened:
			raise RuntimeError("Hub started without host socket")
		self.opened = True
		Thread(target=self.__run, args=()).start()
		return self

	def __run(self):
		tmp = ''
		while True:
			if self.stopped:
				for c in self.connections:
					c.close()
				self.socket.close()
				return

			try:
				s, addr = self.socket.accept()
				if addr not in self.address_connections:
					self.address_connections.append(addr)
					addr, port = addr
					c = connection(self.timeout, self.size)
					c.__receive(s, addr, port)
					self.connections.append(c)
			except socket.timeout:
				continue

	def close(self):
		self.opened = False
		self.stopped = True

	##########################
	### INTERFACE, GETTERS ###
	##########################

	def get_all(self, channel):
		data = []
		for c in self.connections:
			tmp = c.get(channel)
			if tmp is not None:
				data.append(tmp)
		return data

	def get_by_name(self, name, channel):
		return None

	def get_local(self, channel):
		return None

	def get_remote(self, channel):
		return None

	def get_connections(self):
		return self.connections

	##########################
	### INTERFACE, WRITERS ###
	##########################

	def write_all(self, channel, data):
		for c in self.connections:
			c.write(channel, data)
		return self

	def write_to_name(self, name, channel, data):
		return None

	def write_to_local(self, channel, data):
		return None

	def write_to_remote(self, channel, data):
		return None

	def writeImg_ALL(self, data):
		for c in self.connections:
			c.writeImg(data)
		return self
