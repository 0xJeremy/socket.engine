# socket.engine Specification

## Packet Standards

### Packet Types
Each packet of data will be sent with several standarized pieces of information. The first byte of the packet will indicate the type of packet being sent.

```
0 - OPEN: Sent when a new connection is established. This packet also contains information about connection client to server.
1 - CLOSE: Sent when a connection is being broken. Used to indicate closure by both server and client.
2 - CONFIG: Contains information about the configuration of the connection. Ensures settings between client and server are standarized.
3 - MESSAGE: The actual message being sent between applications. Used to send messages by both server and client.
4 - NOOP: A noop packet. Used to force interrupts and callbacks.
```

### Packet Specification
All packets consist of a minimum of 16 bytes. There is no theoretical cap to packet size, but it is nonoptimal to have massive packet sizes. The type of connection formed between the server and the client will dicate the packet size. When messages or information exceed the determined packet size, the packets will be split up and sent individually. User settings will determine if verification is needed from the recipient after each packet, or after messages as a whole.

**ALL PACKETS ARE ENCODED IN BASE64**

### Connection Standard
When a client connects to a server, there is a standardized connection system in place. Similar to the 3 way handshake, this protocol requires verification and achknowledgement before data can be transferred. This ensures a reliable connection.

The protocol is as follows:
CLIENT - Sends OPEN packet with SYN (Synchronized Sequence Number) contents, and information about the connection type. The SYN will contain information about the client, and the requested packet size.
SERVER - Sends OPEN packet with SYN, and ACK (acknowledgement). The ACK will contain information about the server. The server will either confirm or reject the packet size.
CLIENT - Sends OPEN packet with ACK (gotten from server) and confirms the packet.

## Packet Type Specifications

### 0 - OPEN
OPEN packets will contain 16 bytes. The breakdown is as follows:

__Byte Num -> Data__
```
0     -> OPEN
1-6   -> SYN (Synchronized Sequence Number): 6 Bytes
		 	1 = Runtime Random Number
		 	4 = Requested Standard Packet Size
		 	1 = Sending Device Type (if available)
7-12  -> ACK (Acknowledgement): 6 Bytes
		 	1 = Runtime Random Number
		 	4 = Suggested Packet Size
		 	1 = Server Type (if available)
13-15 -> Checksum for entire message (3 bytes)
```

### 1 - CLOSE
[This specification has not yet been outlined.]

### 2 - CONFIG
When a new message is to be passed, a CONFIG packet is sent first. All CONFIG packets are padded to be exactly 16 bytes. This packet will contain the following information:

__Byte Num -> Data__
```
0     -> CONFIG
1     -> Request
         Ex. New msg incoming
             Resend Request
             Change packet size
2-12  -> [Data]
13-15 -> Checksum for entire message (3 bytes)
``` 

### 3 - MESSAGE
The minimum packet size for all MESSAGE packets is 32 bytes. These bytes will be allocated as outlines below. The number `n` denotes the total number of bytes in the actual packet (which may differ from 32 as specified by the client on opening the connection)

__Byte Num -> Data__
```
0        -> MESSAGE
1        -> Type of message (new vs resend)
2-5      -> Number of packets for entire message
6-9      -> Packet number in sequence
10       -> Type of achknowledgement requested
11-(n-3) -> Message
(n-3)-n  -> Checksum for entire message (3 bytes)
```

### 4 - NOOP
This packet will be 16 bytes. The first byte will be the NOOP delimiter, and the rest of the packet will be 0.

__Byte Num -> Data__
```
0    -> NOOP  
2-15 -> 0
```
