from socketengine import client
from socketengine import host
import time
import argparse

TIMEOUT = 0.5
DELAY = 0.5
DEBUG = False

########################
### HELPER FUNCTIONS ###
########################

def s(a=DELAY):
	time.sleep(a)

def report(text):
	global DEBUG
	if DEBUG:
		print("\033[93m[{}]\033[0m".format(text))

def success(text):
	print("\033[32m[{}]\033[0m".format(text))
	s(1)

def initialize():
	h = host(timeout=TIMEOUT)
	c = client(timeout=TIMEOUT)
	report("Sockets initialized")
	h.start()
	c.start()
	report("Sockets started")
	return h, c


text = "Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor match. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. "




RUNS = 10

for i in range(10):
	c = client(addr='127.0.0.1', port=8080)
	c.start()
	c.write("test", text)
	c.close()

print("Wrote test")
c = client(addr='127.0.0.1', port=8080)
c.start()
c.write("verify", RUNS)
print("Wrote verify")


c.close()