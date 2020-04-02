'use strict'

var ip = require('ip');

var data = {
	/////////////////////////
	/// MESSAGE CONSTANTS ///
	/////////////////////////

	NEWLINE : '\n',
	TYPE    : 'type',
	DATA    : 'data',
	IMAGE   : '__image',

	////////////////////////
	/// SOCKET CONSTANTS ///
	////////////////////////

	FAMILY      : 'IPv4',
	ADDR        : ip.address(),
	PORT        : 8080,
	MAXSIZE     : 1500000,
	TIMEOUT     : 0,
	MAX_RETRIES : 99,

	////////////////////
	/// STATUS TYPES ///
	////////////////////
	STATUS    : '__status',
	CLOSING   : '__closing',
	ACK       : '__ack',
	NAME_CONN : '__name_conn',
}

module.exports = exports = data;
