# socket.engine

## Installation

Python:
```
pip install socket.engine
```

This library requires Python3. It was tested extensively on Python 3.7.5 with Ubuntu 19.04.

## Features
Socket.engine enables real-time bidirectional communication between two Python processes. These programs can be run on the same device, or on the same network, or on any device provided there is a port exposed publically from the host. It is optimized for extremely high-speed, reliable information transfer.

Its main features are:

### Speed
Connections are made using TCP sockets and can pass information from processes extremely quickly and reliably. Socket.engine operates using IPv4.

### Easy to use
This library was designed to lower the barrier to entry as much as possible. As such, it was built as a wrapper for network sockets to send massive amounts of information in a very short time.

## How to use

### HOST
```python
from socketengine import host

h = host()
h.start()

while True:
	data = h.get_ALL("test")

	if data is not none:
		for item in data:
			print(item)
			break

h.close()
```
Please Note: Starting a socket.engine socket in Python is a blocking action and will not finish until the socket is opened.

### CLIENT
```python
from socketengine import CLIENT

c = client()
c.start()

c.write("test", "client is connected!")

c.close()
```

Socket.engine will automatically store the most recent piece of data received over a channel. This data is accessible via the `get` method. Socket.engine runs on a separate thread from the rest of your program and will therefore be constantly reading from the data socket.
