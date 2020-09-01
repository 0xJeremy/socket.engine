# socket.engine

### Library Goals

The goals of this library are thus:
- Create a _simple_ and _uniform_ interface for communicating between processes and devices.
- Provide a _fast_ and _reliable_ system with the flexibility for different messaging paradigms.
- Enable advanced communication between multiple devices simultaneously without requiring configuration or care for connectivity.

The goals of this libary are _not_ to:
- Reinvent the wheel. When a system already exists, it will be leveraged.

### Capabilities

The following are a list of capabilities this library will offer
- An advanced and reliable interface allowing the user to send and receive messages without care for size or network speed.
- A standard Publisher-Subscriber (Pub/Sub) model
- A standard Request-Reply model
- Automatic device discovery and connectivity (with the option to enable/disable)
- Access to the internals of the sockets, should users require more advanced options to be applied

### Intentions

The intent of this library is to remain as general as possible. It will, by default, enable extremely high-level communication between arbitrary processes or devices. With that in mind, it will endeavor to remove as much need for care from the user as possible. What this means practically is that should the user simply wish to connect two devices and send the message "Hello", it will not require any configuration out of the box.

However, for more advanced users it will also aim to enable as much configurability as possible and will therefore expose functionality whereever possible or potentially needed.


### Specification

There will be three types of supported communication. Each one will have the appropriate corresponding interface and allow as specific control as possible.

#### One Communication to Rule Them All
There will be a common interface between all socket.engine implementations. At the present, this is Python and Node.js, but can and will be expanded over time. For language specific functions and syntax, see the relevant docs. Below is the core functionality that the library will provide.

All communication for one-to-one, one-to-many, and many-to-many will live in the same class object. The `Transport` object will enable reading and writing to specific remotes, publishing to all remotes, and accepting an arbitrary number of connections. It will automatically open for connections, unless specified otherwise.

This will be achieved by means of the `Transport` object. It will have the following methods:
```
transport(context=zmq.Context(),
          timeout=0.1,
          compression=False,
          defaultAcknowledgement=True,
          basePort=8484)

transport.start() # Begins and enables connections. MUST be called before any other methods.

transport.connect(address,
                  targetBasePort=None,
                  connectionType=Transport.DIRECT)
# Will automatically connect to the remote address. The targetBasePort must ONLY be specified if it is overridden on the remote. Connection types are Transport.DIRECT, Transport.SUBSCRIBER, or Transport.BOTH. DIRECT will form a direct 1-to-1 connection, SUBSCRIBER will attach the subscriber to the remote publisher (the remote MUST have willPublish=True for any effect), and BOTH will attach both.

transport.publish(topic, data)

transport.subscribe(topic)

transport.send(topic,
               data,
               routingID=None,
               requireAcknowledgement=defaultAcknowledgement)

transport.get(topic, routingID=None) # This is an abstraction from .recv()

transport.close()
```

The user may choose to _override_ the internal ports used in a Transport, but by default they will be specified such that each transport will correctly bind to the remote address.
*NOTE:* If you are unsure about overriding a socket port defualt, do not change them.
The default PUB/SUB socket will use port `8484`
The default PAIR socket will use ports `8485 - 8485+n` where `n` is the number of maximum direct connections allowed.

