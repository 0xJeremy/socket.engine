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

var TYPE_LOCAL = 1;
var TYPE_REMOTE = 2;

////////////////////////
/// CONNECTION CLASS ///
////////////////////////

function _connection(socket, address, timeout, maxSize) {
	EventEmitter.call(this);
	this.name = name;
	this.socket = null;
	this.addr = null;
	this.port = null;
	this.canWrite = true;
	this.channels = {};
	this.timeout = timeout;
	this.stopped = false;
	this.opened = false;
	this.type = null;
	this.maxSize = maxSize;
	this.lastData = new Date().getTime();
	this.msgBuffer = '';
	this.listener = null;

	this.receive = function(socket, addr, port) {
		this.socket = socket;
		this.addr = addr;
		this.port = port;
		this.type = TYPE_REMOTE;
		this.opened = true;
		this.__start();
	}

	this.__start = function() {
		this.__run();
	}

	//////////////////////
	/// SOCKET ACTIONS ///
	//////////////////////
	this.__run = function() {
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
	}
	

	this.__cascase = function(mtype, mdata) {
		if(mtype == ACK) {
			this.canWrite = true;
		}
		if(mtype == STATUS) {
			if(mdata == CLOSING) {
				this.__close();
			}
		}
		if(mtype == NAME_CONN) {
			this.name = mdata;
		}
		if(mtype == IMAGE) {
			this.write(ACK, ACK);
		}
	}

	this.__close = function() {
		this.opened = false;
		this.stopped = true;
		this.socket.destroy();
	}

	this._reset = function() {
		// this.msgBuffer = '';
		// this.lastData = new Date().getTime();
		// this.write(ACK, 'True');
		var op = null;
	}

	/////////////////
	/// INTERFACE ///
	/////////////////

	this.connect = function(name, addr, port) {
		this.name = name;
		this.addr = addr;
		this.port = port;
		while(true) {
			try {
				this.socket.connect(this.port, this.addr, () => {
					this.emit('connected');
				});
				break;
			} catch(err) { }
		}
		this.type = TYPE_LOCAL;
		this.opened = true;
		this.write(NAME_CONN, this.name);
		this.__start()
	}

	this.get = function(channel) {
		return this.channels[channel];
	}

	this.getImg = function() {
		return this.channels[IMAGE]
	}

	this.write = function(dataType, data) {
		var msg = {
			'type': dataType.replace('\n', ''),
			'data': data.replace('\n', '')
		};
		this.socket.write(JSON.stringify(msg) + NEWLINE);
	}

	this.close = function() {
		try {
			this.write(STATUS, CLOSING)
		} catch { }
		this.__close()
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

///////////////////////////////////////////////////////////////

/////////////////
/// HUB CLASS ///
/////////////////

function host(addr=ADDR, port=PORT, maxSize=MAXSIZE, timeout=TIMEOUT) {
	EventEmitter.call(this);
	this.net = require('net');

	this.socket = null;
	// this.userDefinedPort = (port == null);
	this.port = port;
	this.timeout = timeout;
	this.maxSize = maxSize;
	this.connections = []
	this.address_connections = []
	this.stopped = false;
	this.opened = false;

	this.socketpath = {
		'port': this.port,
		'family': FAMILY,
		'address': this.addr
	};
	this.listener = null;


	this.__open();
	this.__start();

	

	//////////////
	/// SERVER ///
	//////////////

	this.__open = function() {
		this.server.listen(this.socketpath.port, this.socketpath.address);
		this.opened = true;
		return this;
	}

	this.__start = function() {
		this.__run();
	}

	this.__run = function() {
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
	}

	this.connect = function(name, addr, port) {
		var c = new connection(this.timeout, this.size);
		c.connect(name, addr, port);
		this.connections.push(c);
		return this;
	}

	this.close = function() {
		for(var i = 0; i < this.clients.length; i++) {
			this.clients[i].close();
		}
	}

	this.getConnections = function() {
		return this.connections;
	}

	//////////////////////////
	/// INTERFACE, GETTERS ///
	//////////////////////////

	this.get_all = function(channel) {
		var data = [];
		for(var i = 0; i < this.clients.length; i++) {
			var tmp = this.clients[i].get(channel)
			if(tmp != undefined) {
				data.push(tmp);
			}
		}
		return data;
	}

	this.get_by_name = function(name, channel) {
		var data = [];
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].name == name) {
				var tmp = this.clients[i].get(channel)
				if(tmp != undefined) {
					data.push(tmp);
				}
			}
		}
		return data;
	}

	this.get_local = function(channel) {
		var data = [];
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].type == TYPE_LOCAL) {
				var tmp = this.clients[i].get(channel)
				if(tmp != undefined) {
					data.push(tmp);
				}
			}
		}
		return data;
	}

	this.get_remote = function(channel) {
		var data = [];
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].type == TYPE_REMOTE) {
				var tmp = this.clients[i].get(channel)
				if(tmp != undefined) {
					data.push(tmp);
				}
			}
		}
		return data;
	}

	//////////////////////////
	/// INTERFACE, WRITERS ///
	//////////////////////////

	this.write_all = function(channel, data) {
		for(var i = 0; i < this.clients.length; i++) {
			this.clients[i].write(channel, data);
		}
		return this;
	}

	this.write_to_name = function(name, channel, data) {
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].name == name) {
				this.clients[i].write(channel, data);
			}
		}
		return this;
	}

	this.write_to_local = function(channel, data) {
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].type == TYPE_REMOTE) {
				this.clients[i].write(channel, data);
			}
		}
		return this;
	}

	this.write_to_remote = function(channel, data) {
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].type == TYPE_LOCAL) {
				this.clients[i].write(channel, data);
			}
		}
		return this;
	}

	this.write_image_all = function(data) {
		for(var i = 0; i < this.clients.length; i++) {
			this.clients[i].writeImg(data);
		}
		return this;
	}

	this.write_image_to_name = function(name, data) {
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].name == name) {
				this.clients[i].writeImg(data);
			}
		}
		return this;
	}

	this.write_image_to_local = function(name, data) {
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].type == TYPE_REMOTE) {
				this.clients[i].writeImg(data);
			}
		}
		return this;
	}

	this.write_image_to_remote = function(name, data) {
		for(var i = 0; i < this.clients.length; i++) {
			if(this.clients[i].type == TYPE_LOCAL) {
				this.clients[i].writeImg(data);
			}
		}
		return this;
	}

}

inherits(host, EventEmitter);

module.exports = exports = host;
