# socket.engine

## Installation

Node.js:
```
npm install socket.engine
```

This library was tested with Node.js v10.15.2 on Ubuntu 19.04.

## How to use

```javascript
// Program 1
var hub = require('./hub');

h = new hub(8080)

h.on("connection", (data) => {
	console.log("Hub connected!");
});

h.on("hello", (data) => {
	console.log(data);
	h.close();
});
```

```javascript
// Program 2
var hub = require('./hub');

h = new hub(8081)

h.connect("hello!", "127.0.0.1", 8080);

h.write_all("Hello there!");

h.close();
```

## Documentation

#### Hub

Hub Constructor:
```
hub(port=8080, mazSize=1500000, timeout=0)
	port = Port connection to use with socket
	maxSize = The maximum buffer size before automatically being reset (generally doesn't need to be changed)
	timeout = If non-zero, will automatically clear the buffer on each timeout interval (measured in seconds)
```
Hub Methods:
```
hub.connect(name, addr, port):
	Connects to another port. This connection is named 'name', and the target is the (addr, port) specified.
hub.close():
	Closes the hub and all connections.
hub.getConnections():
	Returns all the connections to the hub as 'connection' objects.
hub.get_all(channel):
	Reads all data from a specified channel. Returns a list of all responses (or [] if no responses)
hub.get_by_name(name, channel):
	Reads all data from a named socket by channel. Returns a list of all responses (or [] if no responses)
hub.get_local(channel):
	Reads all data from locally hosted sockets. Returns a list of all responses (or [] if no responses)
hub.get_remote(channel):
	Reads all data from remote hosted sockets. Returns a list of all responses (or [] if no respones)
hub.write_all(channel, data):
	Writes to all connected hubs via the 'channel' with data.
hub.write_to_name(name, channel, data):
	Writes to all connected sockets with the specified name.
hub.write_to_local(channel, data):
	Writes to all locally hosted sockets.
hub.write_to_remote(channel, data):
	Writes to all remotely hosted sockets.
hub.write_image_all(data):
	Writes an image to all connected sockets.
hub.write_image_to_name(name, data):
	Writes an image to all sockets with a specified name.
hub.write_image_to_local(data):
	Writes an image to all locally hosted sockets.
hub.write_image_to_remote(data):
	Writes an image to all remotely hosted sockets.
```

#### Connection

Connection Constructor:
```
connection(name, timeout=0, maxSize=1500000)
	name = the name of the socket
	timeout = If non-zero, will automatically clear the buffer on each timeout interval (measured in seconds)
	size = Default read size of socket
```
Connection Methods:
```
connection.connect(name, addr, port):
	Initiates a connection to a remote hub. Names the socket with the given 'name', and connects to the (addr, port).
connection.get(channel):
	Gets data from a channel if it exists. Returns None if no data exists on channel.
connection.getImg():
	Gets an from the socket if one exists. Returns None if one does not exist.
connection.write(channel, data):
	Writes data over a specified channel with the given data.
connection.writeImg(data):
	Writes an image over the socket. Optimized for images specifically.
connection.close():
	Closes the socket connection.
```
