#!/usr/bin/env python3

import sys
import os
import unittest
import time

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

# pylint: disable=wrong-import-position, invalid-name
from socketengine import Hub
from socketengine import Transport

TIMEOUT = 0.5
DELAY = 0.5
CHANNEL = 'Test'


def s(a=DELAY):
    time.sleep(a)


def success(message):
    print('\033[32m[{}]\033[0m'.format(message))


# pylint: disable=unused-variable
class TestTransportMethods(unittest.TestCase):
    def testConstructor(self):
        transport = Transport('test')
        self.assertTrue(transport.canWrite)
        self.assertFalse(transport.stopped)
        self.assertFalse(transport.opened)

    def testHubTransportSetup(self):
        start = time.time()
        hubOne = Hub(timeout=TIMEOUT)
        hubTwo = Hub(timeout=TIMEOUT)
        self.assertTrue(hubOne.opened)
        self.assertFalse(hubOne.stopped)
        self.assertTrue(hubTwo.opened)
        self.assertFalse(hubTwo.stopped)
        hubOne.connect(CHANNEL, '127.0.0.1', hubTwo.port)
        s(1)
        self.assertEqual(len(hubOne.transports), 1)
        self.assertEqual(len(hubTwo.transports), 1)
        s(0.5)
        hubOne.close()
        hubTwo.close()
        s(0.5)
        self.assertFalse(hubOne.opened)
        self.assertTrue(hubOne.stopped)
        self.assertFalse(hubTwo.opened)
        self.assertTrue(hubTwo.stopped)
        success('Hub Connection Setup Test Passed ({:.5f} sec)'.format(time.time() - start))


if __name__ == '__main__':
    unittest.main()
