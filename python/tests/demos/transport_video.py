#!/usr/bin/env python3

# pylint: disable=no-member, wrong-import-position
import sys
import os
import argparse
import cv2

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from socketengine import Transport

COLOR = False
SIZE = (320, 240)


def sendVideo():
    transport = Transport('video')
    transport.waitForConnection(8080)
    cam = cv2.VideoCapture(2)
    while True:
        _, frame = cam.read()
        if not COLOR:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, SIZE)
        cv2.imshow('Sending', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            transport.close()
            break
        transport.writeImage(frame)


def getVideo():
    transport = Transport('video')
    transport.connect('video', '127.0.0.1', 8080)
    while transport.getImage() is None:
        pass
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            transport.close()
            break
        cv2.imshow('Stream', transport.getImage())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='socket.engine Hub Video tester')
    parser.add_argument('-s', '--send', help='Begins streaming video Hub', action='store_true')
    parser.add_argument(
        '-g', '--get', help='Begins retrieving video Hub stream', action='store_true',
    )
    parser.add_argument('-c', '--color', help='Sends in color', action='store_true')
    args = parser.parse_args()
    if args.send is True and args.get is True:
        print('Error. Specify only send or get.')
        sys.exit()
    if args.color is True:
        COLOR = True
    if args.send:
        sendVideo()
    if args.get:
        getVideo()
