'use strict'

var EventEmitter = require('events').EventEmitter;
var inherits = require('util').inherits;
var { decomeImg } = require('./common');

/////////////////
/// CONSTANTS ///
/////////////////

const { ACK, NEWLINE } = require('./constants');
const { IMAGE, TYPE, DATA, FAMILY } = require('./constants');
const { PORT, TIMEOUT, MAXSIZE } = require('./constants');
const { STATUS, CLOSING, NAME_CONN } = require('./constants');
const { MAX_RETRIES } = require('./constants');

var TYPE_LOCAL = 1;
var TYPE_REMOTE = 2;

///////////////////////////////////////////////////////////////

////////////////////////
/// CONNECTION CLASS ///
////////////////////////

function _connection(name, timeout=TIMEOUT, maxSize=MAXSIZE) {
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
						this.__cascade(msg[TYPE], msg[DATA]);
						if(msg[TYPE] == IMAGE) {
							this.channels[IMAGE] = decodeImg(msg[DATA]);
						} else {
							this.channels[msg[TYPE]] = msg[DATA];
						}

						this.emit(msg[TYPE], msg[DATA]);
						this.emit('data', msg);
						this.__reset();
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
	

	this.__cascade = function(mtype, mdata) {
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

	this.__reset = function() {
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
		this.__start();
		this.write(NAME_CONN, this.name);
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

	this.writeImg = function(data) {
		if(this.canWrite && this.opened) {
			this.canWrite = false;
			var msg = {
				'type': IMAGE,
				'data': data.replace('\n', '')
			};
			this.socket.write(JSON.stringify(msg) + NEWLINE);
		}
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

function host(port=PORT, maxSize=MAXSIZE, timeout=TIMEOUT) {
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

	//////////////
	/// SERVER ///
	//////////////

	this.__open = function() {
		this.server = this.net.createServer((socket) => {
			this.listener = socket;
		});
		this.server.listen(this.socketpath.port, this.socketpath.address);
		this.opened = true;
		return this;
	}

	this.__start = function() {
		this.__run();
	}

	this.__run = function() {

		this.server.on('connection', (socket) => {
			for(var i = 0; i < this.address_connections.length; i++) {
				if(this.address_connections[i] === socket) {
					return
				}
			}
			this.address_connections.push(socket);
			var c = new connection(null, this.timeout, this.maxSize);
			c.receive(socket, socket.localAddress, socket.localPort);
			this.connections.push(c)
			c.on('data', (msg) => {
				this.emit(msg['type'], this.get_all(msg['type']));
			});
			c.on('error', (err) => {
				this.emit('warning', err);
			});
			c.on('end', () => {
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

	this.__open();
	this.__start();

}

inherits(host, EventEmitter);

module.exports = exports = host;
