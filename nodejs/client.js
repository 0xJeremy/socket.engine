'use strict'

var EventEmitter = require('events').EventEmitter;
var inherits = require('util').inherits;
var ip = require('ip');

/////////////////
/// CONSTANTS ///
/////////////////

var STOP = 'STOP';
var ACK = 'ACK';
var IMAGE = 'image';
var NEWLINE = '\n';

var ADDR = ip.address();
var PORT = 8080;
var MAXSIZE = 1500000;

////////////////////
/// CLIENT CLASS ///
////////////////////

function client(addr=ADDR, port=PORT) {
	EventEmitter.call(this);
	this.net = require('net');

	this.address = address;
	this.port = port;
	this.socket = new this.net.Socket();
	this.msgBuffer = '';
	this.channels = {};

	//////////////////////
	/// SOCKET ACTIONS ///
	//////////////////////

	this.start = function() {
		this.socket.connect(this.port, this.addr, () => {
			this.emit('connected');
		})

		this.socket.on('data', (bytes) => {
			this.msgBuffer += bytes.toString();
			if(this.msgBuffer != '' && this.msgBuffer != '\n') {
				var data = this.msgBuffer.split('\n');
				for(var i = 0; i < data.length; i++) {
					try {
						var msg = JSON.parse(data[i]);
						this.channels[msg['type']] = msg['data'];

						if(msg['type'] == IMAGE) {
							if(base64.test(msg['data'])) {
								this.emit(msg['type'], msg['data']);
							}
						} else {
							this.emit(msg['type'], msg['data']);
						}
						this.emit('data', msg);
					} catch(err) { };
				}
			}
		});

		this.socket.on('end', () => {
			this.emit('end');
		});

		this.socket.on('error', (err) => {
			this.emit('error', err);
		});
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
		this.socket.write(JSON.stringify(msg));
	}

	this.close = function() {
		this.socket.destroy();
	}

}

inherits(client, EventEmitter);

module.exports = exports = client;
