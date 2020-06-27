import cv2
import socket
import base64
import numpy as np


def encodeImg(img):
    return base64.b64encode(cv2.imencode(".png", img)[1])


def decodeImg(img):
    return cv2.imdecode(
        np.fromstring(base64.b64decode(img), dtype=np.uint8), cv2.IMREAD_ANYCOLOR
    )


def generateSocket(timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return s
