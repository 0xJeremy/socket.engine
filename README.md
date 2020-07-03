<div align="center">
  <img src="https://raw.githubusercontent.com/0xJeremy/socket.engine/master/graphics/Logo.png">
</div>

## Installation

[Python](https://pypi.org/project/socket.engine/):

```
pip install socket.engine
```

[Node.js](https://www.npmjs.com/package/socket.engine):

```
npm install socket.engine
```

This library requires Python3. It was tested extensively on Python 3.7.5 and Node.js v10.15.2 with Ubuntu 19.04.

## Features

Socket.engine enables real-time bidirectional communication between Python and Node.js processes. The interface between these languages is nearly identical allowing hosts and clients to be from either language. These programs can be run on the same device, or on the same network, or on any device provided there is a port exposed publically from the host. It is optimized for extremely high-speed, reliable information transfer.

Its main features are:

#### Speed

Connections are made using TCP sockets and can pass information from processes extremely quickly and reliably. Socket.engine operates using IPv4.

#### Easy to use

This library was designed to lower the barrier to entry as much as possible. As such, it was built as a wrapper for network sockets to send massive amounts of information in a very short time.

## Documentation

[Python Documentation](https://github.com/0xJeremy/socket.engine/blob/master/python/README.md)

[Node.js Documentation](https://github.com/0xJeremy/socket.engine/blob/master/nodejs/README.md)
