import socket
import base64
from uuid import uuid4
import cv2
import numpy as np

# pylint: disable=no-member, unused-variable
def encodeImg(img):
    return base64.b64encode(cv2.imencode(".png", img)[1])


def decodeImg(img):
    return cv2.imdecode(np.frombuffer(base64.b64decode(img), dtype=np.uint8), cv2.IMREAD_ANYCOLOR,)


def generateSocket(timeout):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock


def getUUID():
    return str(uuid4())


# pylint: disable=fixme
# TODO: Make this less fragile? Use socket.bind_to_random_port with zmq?
def getOpenPort():
    sock = socket.socket()
    sock.bind(('', 0))

    _, port = sock.getsockname()
    sock.close()

    return port


def baseToPubSubPort(base):
    return base + 1
