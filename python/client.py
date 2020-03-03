import socket
from threading import Thread, Lock
import cv2
import base64
from json import dumps as dictToJson
from json import loads as jsonToDict

#################
### CONSTANTS ###
#################

ACK = 'ACK'
NEWLINE = '\n'.encode()
IMG_MSG_S = '{"type": "image", "data": "'.encode()
IMG_MSG_E = '"}'.encode()

ADDR = '127.0.0.1'
PORT = 8080
TIMEOUT = 200
SIZE = 256

####################
### CLIENT CLASS ###
####################

class client:
	def __init__(self, addr='127.0.0.1', port=8080):
		self.addr = addr
		self.port = port
		self.canWrite = True
		self.channels = {}
		self.lock = Lock()
		self.opened = False
		self.stopped = False
		self.open()
		self.start()

	def open(self):
		while True:
			try:
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.socket.setdefaulttimeout(self.timeout)
				self.socket.connect((self.addr, self.port))
				break
			except: continue
		self.opened = True

	def start(self):
		Thread(target=self.run, args=()).start()
		return self

	def run(self):
		tmp = ''
		while True:
			if self.stopped:
				return

			try:
				tmp += self.socket.recv(self.size).decode()
				msg = jsonToDict(tmp)
				self.channels[msg['type']] = msg['data']
				if(msg['type'] == ACK):
					self.canWrite = True
				tmp = ''
			except: continue

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
		self.opened = False
		self.stopped = True
