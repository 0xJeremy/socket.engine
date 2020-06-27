'use strict'

var EventEmitter = require('events').EventEmitter;
var inherits = require('util').inherits;
var Transport = require('./transport');

/////////////////
/// CONSTANTS ///
/////////////////

const {
	FAMILY, PORT, TIMEOUT, MAXSIZE, TYPE_LOCAL, TYPE_REMOTE
} = require('./constants');

///////////////////////////////////////////////////////////////

/////////////////
/// HUB CLASS ///
/////////////////

function Hub(port=PORT, maxSize=MAXSIZE, timeout=TIMEOUT) {
	EventEmitter.call(this);
	this.net = require('net');

	this.socket = null;
	this.port = port;
	this.timeout = timeout;
	this.maxSize = maxSize;
	this.transports = []
	this.transportAddresses = []
	this.stopped = false;
	this.opened = false;

	this.socketpath = {
		'port': this.port,
		'family': FAMILY,
		'address': '127.0.0.1'
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

	this.__addListeners = function(t) {
		this.transports.push(t);
		t.on('data', (msg) => {
			this.emit(msg['type'], this.get_all(msg['type']));
		});
		t.on('error', (err) => {
			this.emit('warning', err);
		});
		t.on('end', () => {
			this.emit('end');
		});
		this.emit('connection', t);
	}

	this.__run = function() {

		this.server.on('connection', (socket) => {
			for(var i = 0; i < this.transportAddresses.length; i++) {
				if(this.transportAddresses[i] === socket) {
					return
				}
			}
			this.transportAddresses.push(socket);
			var t = new Transport(null, this.timeout, this.maxSize);
			t.receive(socket, socket.localAddress, socket.localPort);
			this.__addListeners(t);
		});
	}

	this.connect = function(name, addr, port) {
		var t = new Transport(this.timeout, this.size);
		t.connect(name, addr, port);
		this.__addListeners(t);
		return this;
	}

	this.close = function() {
		for(var i = 0; i < this.transports.length; i++) {
			this.transports[i].close();
		}
		this.stopped = true;
		this.opened = false;
	}

	this.getConnections = function() {
		return this.transports;
	}

	//////////////////////////
	/// INTERFACE, GETTERS ///
	//////////////////////////

	this.get_all = function(channel) {
		var data = [];
		for(var i = 0; i < this.transports.length; i++) {
			var tmp = this.transports[i].get(channel);
			if(tmp != undefined) {
				data.push(tmp);
			}
		}
		return data;
	}

	this.get_by_name = function(name, channel) {
		var data = [];
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].name == name) {
				var tmp = this.transports[i].get(channel);
				if(tmp != undefined) {
					data.push(tmp);
				}
			}
		}
		return data;
	}

	this.get_local = function(channel) {
		var data = [];
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].type == TYPE_LOCAL) {
				var tmp = this.transports[i].get(channel);
				if(tmp != undefined) {
					data.push(tmp);
				}
			}
		}
		return data;
	}

	this.get_remote = function(channel) {
		var data = [];
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].type == TYPE_REMOTE) {
				var tmp = this.transports[i].get(channel);
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
		for(var i = 0; i < this.transports.length; i++) {
			this.transports[i].write(channel, data);
		}
		return this;
	}

	this.write_to_name = function(name, channel, data) {
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].name == name) {
				this.transports[i].write(channel, data);
			}
		}
		return this;
	}

	this.write_to_local = function(channel, data) {
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].type == TYPE_REMOTE) {
				this.transports[i].write(channel, data);
			}
		}
		return this;
	}

	this.write_to_remote = function(channel, data) {
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].type == TYPE_LOCAL) {
				this.transports[i].write(channel, data);
			}
		}
		return this;
	}

	this.write_image_all = function(data) {
		for(var i = 0; i < this.transports.length; i++) {
			this.transports[i].writeImg(data);
		}
		return this;
	}

	this.write_image_to_name = function(name, data) {
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].name == name) {
				this.transports[i].writeImg(data);
			}
		}
		return this;
	}

	this.write_image_to_local = function(data) {
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].type == TYPE_REMOTE) {
				this.transports[i].writeImg(data);
			}
		}
		return this;
	}

	this.write_image_to_remote = function(data) {
		for(var i = 0; i < this.transports.length; i++) {
			if(this.transports[i].type == TYPE_LOCAL) {
				this.transports[i].writeImg(data);
			}
		}
		return this;
	}

	this.__open();
	this.__start();

}

inherits(Hub, EventEmitter);

module.exports = exports = Hub;
