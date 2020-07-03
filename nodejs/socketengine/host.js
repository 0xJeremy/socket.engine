'use strict';

const EventEmitter = require('events').EventEmitter;
const inherits = require('util').inherits;
const ip = require('ip');

// ///////////////
// / CONSTANTS ///
// ///////////////

const IMAGE = 'image';
const NEWLINE = '\n';
const base64 = new RegExp(
    '^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$',
);
const FAMILY = 'IPv4';

const ADDR = ip.address();
const PORT = 8080;
const MAXSIZE = 1500000;
const TIMEOUT = 0;

// //////////////////////
// / CONNECTION CLASS ///
// //////////////////////

function _connection(socket, address, timeout, maxSize) {
  EventEmitter.call(this);
  this.socket = socket;
  this.address = address;
  this.timeout = timeout;
  this.maxSize = maxSize;
  this.lastData = new Date().getTime();
  this.msgBuffer = '';
  this.channels = {};
  this.listener = null;

  // ////////////////////
  // / SOCKET ACTIONS ///
  // ////////////////////

  this.socket.on('data', (bytes) => {
    this.msgBuffer += bytes.toString();
    if (this.msgBuffer != '' && this.msgBuffer != '\n') {
      const data = this.msgBuffer.split('\n');
      for (let i = 0; i < data.length; i++) {
        try {
          if (data[i] == '') {
            continue;
          }
          const msg = JSON.parse(data[i]);
          this.channels[msg['type']] = msg['data'];
          if (msg['type'] == IMAGE) {
            if (base64.test(msg['data'])) {
              this.emit(msg['type'], msg['data']);
            }
          } else {
            this.emit(msg['type'], msg['data']);
          }
          this.emit('data', msg);
        } catch (err) {}
      }
    }
  });
  this.socket.on('end', () => {
    this.emit('end');
  });

  this.socket.on('error', (err) => {
    this.emit('warning', err);
  });

  // /////////////
  // / METHODS ///
  // /////////////

  this.get = function(channel) {
    return this.channels[channel];
  };

  this.write = function(dataType, data) {
    const msg = {
      type: dataType,
      data: data,
    };
    this.socket.write(JSON.stringify(msg) + NEWLINE);
  };

  this.close = function() {
    this.socket.destroy();
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

inherits(_connection, EventEmitter);

// ////////////////
// / HOST CLASS ///
// ////////////////

function Host(addr = ADDR, port = PORT, maxSize = MAXSIZE, timeout = TIMEOUT) {
  EventEmitter.call(this);
  this.net = require('net');

  this.addr = addr;
  this.port = port;
  this.timeout = timeout;
  this.maxSize = maxSize;

  this.clients = [];
  this.sockets = [];

  this.socketpath = {
    port: this.port,
    family: FAMILY,
    address: this.addr,
  };
  this.listener = null;
  this.opened = false;

  // ////////////
  // / SERVER ///
  // ////////////

  this.server = this.net.createServer((socket) => {
    this.listener = socket;
  });

  this.server.on('connection', (socket) => {
    for (let i = 0; i < this.sockets.length; i++) {
      if (this.sockets[i] === socket) {
        return;
      }
    }
    this.sockets.push(socket);
    const connection = new _connection(
        socket,
        socket.address(),
        this.timeout,
        this.maxSize,
    );
    this.clients.push(connection);
    connection.on('data', (msg) => {
      this.emit(msg['type'], this.get_ALL(msg['type']));
    });
    connection.on('error', (err) => {
      this.emit('warning', err);
    });
    connection.on('end', () => {
      this.emit('end');
    });
  });

  // /////////////
  // / METHODS ///
  // /////////////

  this.start = function() {
    this.server.listen(this.socketpath.port, this.socketpath.address);
    this.opened = true;
    return this;
  };

  this.get_ALL = function(channel) {
    const data = [];
    for (let i = 0; i < this.clients.length; i++) {
      const tmp = this.clients[i].get(channel);
      if (tmp != undefined) {
        data.push(tmp);
      }
    }
    return data;
  };

  this.getClients = function() {
    return this.clients;
  };

  this.write_ALL = function(channel, data) {
    for (let i = 0; i < this.clients.length; i++) {
      this.clients[i].write(channel, data);
    }
    return this;
  };

  this.close = function() {
    for (let i = 0; i < this.clients.length; i++) {
      this.clients[i].close();
    }
  };
}

inherits(Host, EventEmitter);

module.exports = exports = Host;
