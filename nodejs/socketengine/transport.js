'use strict';

const EventEmitter = require('events').EventEmitter;
const inherits = require('util').inherits;
const net = require('net');
const SocketMessage = require('socketmessage').SocketMessage;

// ///////////////
// / CONSTANTS ///
// ///////////////

const {
  ACK,
  NEWLINE,
  IMAGE,
  TYPE,
  DATA,
  TIMEOUT,
  MAXSIZE,
  STATUS,
  CLOSING,
  NAME_CONN,
  TYPE_LOCAL,
  TYPE_REMOTE,
} = require('./constants');

// /////////////////////////////////////////////////////////////

// /////////////////////
// / TRANSPORT CLASS ///
// /////////////////////

function Transport(timeout=TIMEOUT, readSize=Size, useCompression=false, requireAck=false, bufferEnabled=false) {
  EventEmitter.call(this);
  this.name = null;
  this.channels = {};
  // TODO: add socket timeouts
  this.timeout = timeout;
  this.readSize = readSize;
  this.compress = useCompression
  this.writeAvailable = true;
  this.stopped = false;
  this.opened = false;
  this.socket = null;
  this.addr = null;
  this.port = null;
  this.ackRequired = requireAck;
  this.bufferEnabled = bufferEnabled;
  // TODO: add high water mark
  // this.maxSize = maxSize;
  this.lastData = new Date().getTime();
  this.msgBuffer = '';
  this.listener = null;

  this.receive = function(socket, addr, port) {
    this.socket = socket;
    this.addr = addr;
    this.port = port;
    this.__start();
  };

  this.__start = function() {
    this.__run();
  };

  this.__run = function() {
    this.opened = true;
    this.foundDelimiter = false;

    this.socket.on('data', (bytes) => {
      const read = bytes.toString();
      // TODO: add last bit of buffer here
      if (read.includes(DELIMITER)) {
        this.foundDelimiter = true;
      }
      this.msgBuffer += read;

      if (this.msgBuffer != '' && this.foundDelimiter) {
        this.__processMessage();
        this.foundDelimiter = false;
      }

      this.__sendWaitingMessages();
    });
    
    this.socket.on('end', () => {
      this.emit('end');
    });

    this.socket.on('error', (err) => {
      this.emit('warning', err);
    });
  };

  this.__sendWaitingMessages = function() {
    for (let i = 0; i < this.waitingBuffer.length; i++) {
      this.__sendAll(self.waitingBuffer.shift());
    }
  }

  this.__processMessage = function() {
    const messages = this.msgBuffer.split(DELIMITER);
    if (this.compress) {
      // TODO: pull in zlib compression
      throw new Error('Not implemented.');
    }
    for (let i = 0; i < messages.length; i++) {
      const message = new SocketMessage();
      message.ParseFromString(messages[i]);

      if (message.type == IMAGE) {
        this.channels[IMAGE] = decodeImg(message.data)
      } else if (message.data != '') {
        this.channels[message.type] = message.data;
      }

      this.__cascade(message);
      messages[i] = '';
    }
    this.msgBuffer = messages.join('');
  }

  this.__cascade = function(message) {
    meta = message.meta;
    if (meta == ACK) {
      this.writeAvailable = true;
      this.emit('writeAvailable');
    } else if (meta == CLOSING) {
      this.__close();
    } else if (meta == NAME_CONN) {
      this.name = message.data;
      this.emit('name');
    }
    if (message.ackRequired) {
      this.__ack();
    }
  };

  this.__ack = function() {
    this.__writeMeta(ACK)
  }

  this.__writeMeta = function(meta, data=null) {
    const message = new SocketMessage();
    message.meta = meta;
    if (data) {
      message.data = data;
    }
    self.__sendAll(message, true);
  }

  this.__sendAll = function(message, overrideAck=false) {
    // TODO
  }

  this.__close = function() {
    this.opened = false;
    this.stopped = true;
    this.socket.destroy();
  };

  // ///////////////
  // / INTERFACE ///
  // ///////////////

  this.connect = function(name, addr, port) {
    this.name = name;
    this.addr = addr;
    this.port = port;
    this.socket = new net.Socket();
    while (true) {
      try {
        this.socket.connect(this.port, this.addr, () => {
          this.emit('connected');
        });
        break;
      } catch (err) {
        console.log(err);
      }
    }
    this.type = TYPE_LOCAL;
    this.opened = true;
    this.__start();
    this.write(NAME_CONN, this.name);
  };

  this.get = function(channel) {
    return this.channels[channel];
  };

  this.getImg = function() {
    return this.channels[IMAGE];
  };

  this.write = function(dataType, data) {
    const msg = {
      type: dataType.replace('\n', ''),
      data: data.replace('\n', ''),
    };
    this.socket.write(JSON.stringify(msg) + NEWLINE);
  };

  this.writeImg = function(data) {
    if (this.canWrite && this.opened) {
      this.canWrite = false;
      const msg = {
        type: IMAGE,
        data: data.replace('\n', ''),
      };
      this.socket.write(JSON.stringify(msg) + NEWLINE);
    }
  };

  this.close = function() {
    try {
      this.write(STATUS, CLOSING);
    } catch {}
    this.__close();
  };

  // Timeout handler
  if (this.timeout > 0) {
    setInterval(() => {
      if ((new Date().getTime() - this.lastData) / 1000 > this.timeout) {
        if (this.msgBuffer == '') {
          try {
            this.reset();
          } catch (err) {}
        }
      }
    }, this.timeout);
  }
}

inherits(Transport, EventEmitter);

module.exports = exports = Transport;
