# pylint: disable=unused-variable
#########################
### MESSAGE CONSTANTS ###
#########################

NEWLINE = '\n'.encode()
TYPE = 'type'
DATA = 'data'
IMAGE = '__image'
IMG_MSG_S = '{"type": "__image", "data": "'.encode()
IMG_MSG_E = '"}'.encode()

DELIMITER = b'\0\0\0'
DELIMITER_SIZE = len(DELIMITER)

########################
### SOCKET CONSTANTS ###
########################

ADDR = '127.0.0.1'
PORT = 8080
TIMEOUT = 2
SIZE = 256
OPEN = True

####################
### STATUS TYPES ###
####################

STATUS = '__status'
CLOSING = '__closing'
ACK = '__ack'
NAME_CONN = '__name_conn'
