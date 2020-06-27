'use strict'

var EventEmitter = require('events').EventEmitter;
var inherits = require('util').inherits;
var { decomeImg } = require('./common');

/////////////////
/// CONSTANTS ///
/////////////////

const {
	ACK, NEWLINE, IMAGE, TYPE, DATA, FAMILY, PORT, TIMEOUT, MAXSIZE, 
	STATUS, CLOSING, NAME_CONN, TYPE_LOCAL, TYPE_REMOTE
} = require('./constants');

///////////////////////////////////////////////////////////////

///////////////////////
/// TRANSPORT CLASS ///
///////////////////////

function Transport(name, timeout=TIMEOUT, maxSize=MAXSIZE) {
	EventEmitter.call(this);
	this.net = require('net');

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
		this.socket = new this.net.Socket();
		while(true) {
			try {
				this.socket.connect(this.port, this.addr, () => {
					this.emit('connected');
				});
				break;
			} catch(err) {console.log(err) }
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

inherits(Transport, EventEmitter);

module.exports = exports = Transport;
