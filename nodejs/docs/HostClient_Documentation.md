# socket.engine

## Installation

Node.js:
```
npm install socket.engine
```

This library was tested with Node.js v10.15.2 on Ubuntu 19.04.

## How to use

#### Host
```javascript
var host = require('socketengine').host;

var h = new host();
h.start();

h.on("Test", (data) => {
	console.log(data);
	h.write_ALL("Test", data);
});
```

#### Client
```javascript
var client = require('socketengine').client;

var c = new client();
c.start();

c.on("Test", (data) => {
	console.log(data);
});

c.write("Test", "Hello there!");
```

Socket.engine will automatically store the most recent piece of data received over a channel. This data is accessible via the `get` method (on the client side), or the `get_ALL` method (on the host side). Socket.engine is capable of both asynchronous callbacks (triggered by the channel name), or synchronous calls (with the `get` methods).

## Documentation

#### Host

Host Constructor:
```
host(addr=ADDR, port=8080, maxSize=1500000, timeout=0)
	addr = Address to host the socket connection (defaults to device IPv4 address)
	port = Port connection to use with socket
	maxSize = The maximum buffer size before automatically being reset (generally doesn't need to be changed)
	timeout = If non-zero, will automatically clear the buffer on each timeout interval (measured in seconds)
```
Host Methods:
```
host.start():
	Starts the socket server. SHOULD ONLY BE CALLED ONCE
host.get_ALL(channel):
	Reads all data from a specified channel. Returns a list of all responses (or [] if no responses)
host.getClients():
	Returns a list of connected clients as socket objects
host.write_ALL(channel, data):
	Writes data on the specified channel to all clients
host.close():
	Closes the connection with each client
```

#### Client

Client Constructor:
```
client(addr=ADDR, port=8080)
	addr = Address to host the socket connection (defaults to device IPv4 address)
		port = Port connection to use with socket
```
Client Methods:
```
client.get(channel):
	Reads all data from a specified channel
client.write(channel, data):
	Writes data on a specified channel
client.close():
	Closes the connection
```
