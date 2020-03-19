# socket.engine

## Installation

Python:
```
pip install socket.engine
```

This library requires Python3. It was tested extensively on Python 3.7.5 with Ubuntu 19.04.

## How to use

#### Host
```python
from socketengine import host

h = host()
h.start()

while True:
	data = h.get_ALL("test")

	if data is not None:
		for item in data:
			print(item)
			break

h.close()
```
Please Note: Starting a socket.engine socket in Python is a blocking action and will not finish until the socket is opened.

#### Client
```python
from socketengine import client

c = client()
c.start()

c.write("test", "client is connected!")

c.close()
```

Socket.engine will automatically store the most recent piece of data received over a channel. This data is accessible via the `get` method. Socket.engine runs on a separate thread from the rest of your program and will therefore be constantly reading from the data socket.

## Documentation

#### Host

Host Constructor:
```
host(addr='127.0.0.1', port=8080, timeout=2, size=256, open=True)
	addr = Address to host the socket connection
	port = Port connection to use with socket
	timeout = Sets the standard timeout of a socket (in seconds)
	size = Default read size of socket
	open = Open the socket automatically on connection (note: this does not "start" the socket thread)
```
Host Methods:
```
host.set_timeout(time):
	Sets the timeout of a socket (in seconds)
host.start():
	Starts the socket thread. SHOULD ONLY BE CALLED ONCE
host.get_ALL(channel):
	Reads all data from a specified channel. Returns a list of all responses (or [] if no responses)
host.getClients():
	Returns a list of connected clients as socket objects
host.writeLock_ALL(channel, data):
	Writes data on the specified channel to all clients. Uses a lock on each connection
host.write_ALL(channel, data):
	Writes data on the specified channel to all clients
host.writeImgLock_ALL(data): 
	Writes image data over the "image" channel to all clients. This method optimized for sending entire images. Uses a lock on each connection
host.writeImg_ALL(data): 
	Writes image data over the "image" channel to all clients. This method optimized for sending entire images.
host.close(): 
	Closes the connection with each client
```

#### Client
Client Constructor:
```
client(addr='127.0.0.1', port=8080, timeout=2, size=256, open=True)
	addr = Address the host is using
	port = Port connection on host
	timeout = Sets the standard timeout of a socket (in seconds)
	size = Default read size of socket
	open = Open the socket automatically on connection (note: this does not "start" the socket thread)
```
Client Methods:
```
client.set_timeout(time):
	Sets the timeout of a socket (in seconds)
client.start():
	Starts the socket thread. SHOULD ONLY BE CALLED ONCE
client.get(channel):
	Reads all data from a specified channel
client.writeLock(channel, data):
	Writes data on the specified channel. Uses a lock on each connection
client.write(channel, data): 
	Writes data on a specified channel
client.writeImgLock(data):
	Writes image data over the "image" channel. This method optimized for sending entire images. Uses a lock on each connection
client.writeImg(data):
	Writes image data over the "image" channel. This method optimized for sending entire images.
client.close():
	Closes the connection
```
