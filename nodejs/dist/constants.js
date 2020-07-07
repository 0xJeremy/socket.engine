"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TYPE_REMOTE = exports.TYPE_LOCAL = exports.NAME_CONN = exports.ACK = exports.CLOSING = exports.STATUS = exports.MAX_RETRIES = exports.TIMEOUT = exports.MAXSIZE = exports.PORT = exports.ADDR = exports.FAMILY = exports.IMAGE = exports.DATA = exports.TYPE = exports.NEWLINE = void 0;
const ip_1 = require("ip");
// ///////////////////////
// / MESSAGE CONSTANTS ///
// ///////////////////////
exports.NEWLINE = '\n';
exports.TYPE = 'type';
exports.DATA = 'data';
exports.IMAGE = '__image';
// //////////////////////
// / SOCKET CONSTANTS ///
// //////////////////////
exports.FAMILY = 'IPv4';
exports.ADDR = ip_1.address();
exports.PORT = 8080;
exports.MAXSIZE = 1500000;
exports.TIMEOUT = 0;
exports.MAX_RETRIES = 99;
// //////////////////
// / STATUS TYPES ///
// //////////////////
exports.STATUS = '__status';
exports.CLOSING = '__closing';
exports.ACK = '__ack';
exports.NAME_CONN = '__name_conn';
// ///////////
// / ENUMS ///
// ///////////
exports.TYPE_LOCAL = 1;
exports.TYPE_REMOTE = 2;
