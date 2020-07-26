import sys
import os
import time

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

# pylint: disable=wrong-import-position
from socketengine import Router

# pylint: disable=unused-variable, global-statement

TIMEOUT = 0.01
CHANNEL = 'channel'
TEST = 'Test'
TEST_2 = 'Test2'
PORT_TEST = 'test of port 1'
PORT_TEST_2 = 'test of port 2'
MESSAGE = 'message'
HOME = '127.0.0.1'
PORT = 8999
START_TIME = 0


def getUniquePort():
    global PORT
    PORT += 10
    return PORT


def start():
    global START_TIME
    START_TIME = time.time()


def finish(message):
    global START_TIME
    success('{} ({:.5f} sec)'.format(message, time.time() - START_TIME))


def success(message):
    print('\033[32m[{}]\033[0m'.format(message))


def initialize(readSize=256):
    hubOne = Router(timeout=TIMEOUT, readSize=readSize, findOpenPort=True)
    hubTwo = Router(timeout=TIMEOUT, readSize=readSize, findOpenPort=True)
    hubOne.connect(TEST, HOME, hubTwo.port)
    while len(hubOne.transports) == 0 or len(hubTwo.transports) == 0:
        pass
    while not hubOne.transports[0].opened or not hubTwo.transports[0].opened:
        pass
    time.sleep(0.1)
    return hubOne, hubTwo


# pylint: disable=line-too-long

TEXT = 'Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor matchub. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. '
