#!/usr/bin/env python3

import sys
import os

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from socketengine import hub
from socketengine import connection
import cv2
from time import sleep
import argparse

COLOR = False
SIZE = (320, 240)


def send_video():
    h = hub(port=8080)
    print("Started hub on port", h.port)
    h.connect("video", "127.0.0.1", 8081)
    print("Connected!")
    sleep(2)
    c = h.connections[0]
    cam = cv2.VideoCapture(2)
    while True:
        ret, frame = cam.read()
        if not COLOR:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, SIZE)
        cv2.imshow("Sending", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            h.close()
            break
        c.writeImg(frame)


def get_video():
    h = hub(port=8081)
    print("Started hub on port", h.port)
    while h.connections == []:
        pass
    c = h.connections[0]
    print("Starting capture")
    while c.getImg() is None:
        pass
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            h.close()
            break
        cv2.imshow("Stream", c.getImg())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="socket.engine Hub Video tester")
    parser.add_argument(
        "-s", "--send", help="Begins streaming video hub", action="store_true"
    )
    parser.add_argument(
        "-g", "--get", help="Begins retrieving video hub stream", action="store_true"
    )
    parser.add_argument("-c", "--color", help="Sends in color", action="store_true")
    args = parser.parse_args()
    if args.send is True and args.get is True:
        print("Error. Specify only send or get.")
        sys.exit()
    if args.color is True:
        COLOR = True
    if args.send:
        send_video()
    if args.get:
        get_video()
