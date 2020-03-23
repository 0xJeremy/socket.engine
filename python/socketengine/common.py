import cv2
import socket

def encodeImg(img):
	success, encoded_img = cv2.imencode('.png', img)
	return base64.b64encode(encoded_img)

def generateSocket(timeout):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(timeout)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	return s
