#########################
### MESSAGE CONSTANTS ###
#########################

NEWLINE   = '\n'.encode()
IMG_MSG_S = '{"type": "image", "data": "'.encode()
IMG_MSG_E = '"}'.encode()

########################
### SOCKET CONSTANTS ###
########################

ADDR    = '127.0.0.1'
PORT    = 8080
TIMEOUT = 2
SIZE    = 256
OPEN    = True
STATUS  = '__status'

####################
### STATUS TYPES ###
####################

CLOSING = '__closing'
ACK     = '__ack'


