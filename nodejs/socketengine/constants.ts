import { address } from 'ip';

// ///////////////////////
// / MESSAGE CONSTANTS ///
// ///////////////////////

export const NEWLINE = '\n';
export const TYPE = 'type';
export const DATA = 'data';
export const IMAGE = '__image';

// //////////////////////
// / SOCKET CONSTANTS ///
// //////////////////////

export const FAMILY = 'IPv4';
export const ADDR = address();
export const PORT = 8080;
export const MAXSIZE = 1500000;
export const TIMEOUT = 0;
export const MAX_RETRIES = 99;

// //////////////////
// / STATUS TYPES ///
// //////////////////

export const STATUS = '__status';
export const CLOSING = '__closing';
export const ACK = '__ack';
export const NAME_CONN = '__name_conn';

// ///////////
// / ENUMS ///
// ///////////

export const TYPE_LOCAL = 1;
export const TYPE_REMOTE = 2;
