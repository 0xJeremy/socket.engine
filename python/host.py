import socket
from threading import Thread, Lock
import cv2
import base64
from json import dumps as dictToJson
from json import loads as jsonToDict
from json.decoder import JSONDecodeError

#################
### CONSTANTS ###
#################

ACK = 'ACK'
NEWLINE = '\n'.encode()
IMG_MSG_S = '{"type": "image", "data": "'.encode()
IMG_MSG_E = '"}'.encode()

ADDR = '127.0.0.1'
PORT = 8080
TIMEOUT = 2
SIZE = 256

########################
### CONNECTION CLASS ###
########################

class _connection:
	def __init__(self, socket, address, timeout, size):
		self.socket = socket
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
				msg = jsonToDict(tmp)
				self.channels[msg['type']] = msg['data']
				if(msg['type'] == ACK):
					self.canWrite = True
				tmp = ''
			except JSONDecodeError: 
				continue
			except socket.timeout:
				continue

	def get(self, channel):
		if channel in self.channels.keys():
			return self.channels[channel]
		return None

	def encodeImg(self, img):
		success, encoded_img = cv2.imencode('.png', img)
		return base64.b64encode(encoded_img)

	def writeLock(self, channel, data):
		with self.lock:
			self.write(channel, data)

	def write(self, channel, data):
		if self.canWrite:
			self.canWrite = False
			msg = {'type': channel, 'data': data}
			self.socket.sendall(dictToJson(msg).encode() + NEWLINE)

	def writeImgLock(self, data):
		with self.lock:
			self.writeImg(data)

	def writeImg(self, data):
		if self.canWrite:
			self.canWrite = False
			msg = IMG_MSG_S + self.encodeImg(data) + IMG_MSG_E
			self.socket.sendall(msg + NEWLINE)

	def close(self):
		self.stopped = True

##################
### HOST CLASS ###
##################

class host:
	def __init__(self, addr=ADDR, port=PORT, timeout=TIMEOUT, size=SIZE, open=True):
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

	def set_timeout(self, time):
		self.timeout = time

	def open(self):
		while True:
			try:
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.socket.settimeout(self.timeout)
				self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.socket.bind(('', self.port))
				self.socket.listen()
				break
			except OSError as e:
				raise RuntimeError("Socket address in use: {}".format(e))
				return
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
				for c in self.clients:
					c.close()
				self.socket.close()
				return

			try:
				c, addr = self.socket.accept()
				if addr not in self.connections:
					self.connections.append(addr)
					self.clients.append(_connection(c, addr, self.timeout, self.size))
			except socket.timeout:
				continue


	def get_ALL(self, channel):
		data = []
		for c in self.clients:
			tmp = c.get(channel)
			if tmp is not None:
				data.append(tmp)
		return data

	def getClients(self):
		return self.clients

	def writeLock_ALL(self, channel, data):
		for c in self.clients:
			self.writeLock(channel, data)

	def write_ALL(self, channel, data):
		for c in self.clients:
			c.write(channel, data)

	def writeImgLock_ALL(self, data):
		for c in self.clients:
			c.writeImg(data)

	def writeImg_ALL(self, data):
		for c in self.clients:
			c.writeImg(data)

	def close(self):
		self.opened = False
		for c in self.clients:
			c.close()
		self.stopped = True
