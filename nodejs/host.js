'use strict'

var EventEmitter = require('events').EventEmitter;
var inherits = require('util').inherits;
var ip = require('ip');

/////////////////
/// CONSTANTS ///
/////////////////

var STOP = 'STOP';
var ACK = '__ack';
var IMAGE = 'image';
var NEWLINE = '\n';
var base64 = new RegExp('^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$');
var FAMILY = 'IPv4';

var ADDR = ip.address();
var PORT = 8080;
var MAXSIZE = 1500000;
var TIMEOUT = 0;

////////////////////////
/// CONNECTION CLASS ///
////////////////////////

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

	//////////////////////
	/// SOCKET ACTIONS ///
	//////////////////////

	this.socket.on('data', (bytes) => {
		this.msgBuffer += bytes.toString();
		if(this.msgBuffer != '' && this.msgBuffer != '\n') {
			var data = this.msgBuffer.split('\n');
			for(var i = 0; i < data.length; i++) {
				try {
					if(data[i] == '') {
						continue;
					}
					var msg = JSON.parse(data[i]);
					this.channels[msg['type']] = msg['data'];
					if(msg['type'] == IMAGE) {
						if(base64.test(msg['data'])) {
							this.emit(msg['type'], msg['data']);
						}
					} else {
						this.emit(msg['type'], msg['data']);
					}
					this._reset();
					this.emit('data', msg);
				} catch(err) {};
			}
		}
	});
	this.socket.on('end', () => {
			this.emit('end');
		});

	this.socket.on('error', (err) => {
		this.emit('warning', err);
	});

	this._reset = function() {
		// this.msgBuffer = '';
		// this.lastData = new Date().getTime();
		// this.write(ACK, 'True');
		var op = null;
	}

	///////////////
	/// METHODS ///
	///////////////

	this.get = function(channel) {
		return this.channels[channel];
	}

	this.write = function(dataType, data) {
		var msg = {
			'type': dataType,
			'data': data
		};
		this.socket.write(JSON.stringify(msg) + NEWLINE);
	}

	this.close = function() {
		this.socket.destroy();
	}

	// Timeout handler
	if(this.timeout > 0) {
		setInterval( () => {
			if(((new Date().getTime() - this.lastData) / 1000) > this.timeout) {
				if(this.msgBuffer == '') {
					try { this.reset() }
					catch(err) {}
				}
			}
		}, this.timeout);
	}
}

inherits(_connection, EventEmitter);

//////////////////
/// HOST CLASS ///
//////////////////

function host(addr=ADDR, port=PORT, maxSize=MAXSIZE, timeout=TIMEOUT) {
	EventEmitter.call(this);
	this.net = require('net');

	this.addr = addr;
	this.port = port;
	this.timeout = timeout;
	this.maxSize = maxSize;

	this.clients = [];
	this.sockets = [];
	
	this.socketpath = {
		'port': this.port,
		'family': FAMILY,
		'address': this.addr
	};
	this.listener = null;
	this.opened = false;

	//////////////
	/// SERVER ///
	//////////////

	this.server = this.net.createServer((socket) => {
		this.listener = socket;
	});

	this.server.on('connection', (socket) => {
		for(var i = 0; i < this.sockets.length; i++) {
			if(this.sockets[i] === socket) {
				return
			}
		}
		this.sockets.push(socket);
		var connection = new _connection(socket, socket.address(), this.timeout, this.maxSize)
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

	///////////////
	/// METHODS ///
	///////////////

	this.start = function() {
		this.server.listen(this.socketpath.port, this.socketpath.address);
		this.opened = true;
		return this;
	}

	this.get_ALL = function(channel) {
		var data = [];
		for(var i = 0; i < this.clients.length; i++) {
			var tmp = this.clients[i].get(channel)
			if(tmp != undefined) {
				data.push(tmp);
			}
		}
		return data;
	}

	this.getClients = function() {
		return this.clients;
	}

	this.write_ALL =function(channel, data) {
		for(var i = 0; i < this.clients.length; i++) {
			this.clients[i].write(channel, data);
		}
		return this;
	}

	this.close = function() {
		for(var i = 0; i < this.clients.length; i++) {
			this.clients[i].close();
		}
	}
}

inherits(host, EventEmitter);

module.exports = exports = host;
