#########################
### MESSAGE CONSTANTS ###
#########################

NEWLINE = "\n".encode()
TYPE = "type"
DATA = "data"
IMAGE = "__image"
IMG_MSG_S = '{"type": "__image", "data": "'.encode()
IMG_MSG_E = '"}'.encode()

########################
### SOCKET CONSTANTS ###
########################

ADDR = "127.0.0.1"
PORT = 8080
TIMEOUT = 2
SIZE = 256
OPEN = True
MAX_RETRIES = 99

####################
### STATUS TYPES ###
####################

STATUS = "__status"
CLOSING = "__closing"
ACK = "__ack"
NAME_CONN = "__name_conn"
