"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
exports.__esModule = true;
exports.Transport = void 0;
var events_1 = require("events");
var util_1 = require("util");
var socketmessage_1 = require("./socketmessage");
var constants_1 = require("./constants");
var DELIMITER = '\0\0\0';
var Transport = /** @class */ (function (_super) {
    __extends(Transport, _super);
    function Transport(useCompression, requireAck, bufferEnabled) {
        var _this = _super.call(this) || this;
        _this.useCompression = useCompression;
        _this.requireAck = requireAck;
        _this.bufferEnabled = bufferEnabled;
        _this.channels = new Map();
        _this.writeAvailable = true;
        _this.foundDelimiter = false;
        _this.opened = false;
        _this.msgBuffer = '';
        _this.waitingBuffer = [];
        _this.name = undefined;
        _this.addr = undefined;
        _this.port = undefined;
        return _this;
    }
    Transport.prototype.connect = function (name, addr, port) {
        var _this = this;
        this.name = name;
        this.addr = addr;
        this.port = port;
        while (true) {
            try {
                this.socket.connect(this.port, this.addr, function () {
                    _this.emit('connected');
                });
                break;
            }
            catch (err) {
                console.log(err);
            }
        }
        this.opened = true;
        this.__start();
        this.__writeMeta(constants_1.NAME_CONN, this.name);
    };
    Transport.prototype.receive = function (socket, addr, port) {
        this.socket = socket;
        this.addr = addr;
        this.port = port;
        return this.__start();
    };
    Transport.prototype.get = function (channel) {
        return this.channels.get(channel);
    };
    Transport.prototype.getImg = function () {
        return this.channels.get(constants_1.IMAGE);
    };
    Transport.prototype.write = function (channel, data) {
        var message = new socketmessage_1.SocketMessage();
        message.setType(channel);
        message.setData(data);
        this.__sendAll(message);
    };
    Transport.prototype.writeImage = function (data) {
        var message = new socketmessage_1.SocketMessage();
        message.setType(constants_1.IMAGE);
        message.setData(data);
        this.__sendAll(message);
    };
    Transport.prototype.close = function () {
        try {
            this.__writeMeta(constants_1.CLOSING);
        }
        catch (_a) { }
        this.__close();
    };
    Transport.prototype.__start = function () {
        return this.__run();
    };
    Transport.prototype.__run = function () {
        var _this = this;
        this.opened = true;
        this.foundDelimiter = false;
        if (!this.socket) {
            throw new Error('Unable to start Transport; socket does not exist.');
        }
        this.socket.on('data', function (bytes) {
            var read = bytes.toString();
            // TODO: add last bit of buffer here
            if (read.includes(DELIMITER)) {
                _this.foundDelimiter = true;
            }
            _this.msgBuffer += read.toString();
            if (_this.msgBuffer != '' && _this.foundDelimiter) {
                _this.__processMessage();
                _this.foundDelimiter = false;
            }
            _this.__sendWaitingMessages();
        });
        this.socket.on('end', function () {
            _this.emit('end');
        });
        this.socket.on('error', function (err) {
            _this.emit('warning', err);
        });
    };
    Transport.prototype.__sendWaitingMessages = function () {
        for (var i = 0; i < this.waitingBuffer.length; i++) {
            var message = this.waitingBuffer.shift();
            if (message) {
                this.__sendAll(message);
            }
        }
    };
    Transport.prototype.__processMessage = function () {
        var messages = this.msgBuffer.split(DELIMITER);
        if (this.useCompression) {
            // TODO: pull in zlib compression
            throw new Error('Not implemented.');
        }
        for (var i = 0; i < messages.length; i++) {
            // TODO: Make this more efficient
            var encoder = new util_1.TextEncoder();
            var message = socketmessage_1.SocketMessage.deserializeBinary(encoder.encode(messages[i]));
            if (message.getType() == constants_1.IMAGE) {
                // this.channels.set(IMAGE, decodeImg(message.data));
                this.channels.set(constants_1.IMAGE, message.getData());
            }
            else if (message.getData() != '') {
                this.channels.set(message.getType(), message.getData());
            }
            this.__cascade(message);
            messages[i] = '';
        }
        this.msgBuffer = messages.join('');
    };
    Transport.prototype.__cascade = function (message) {
        var meta = message.getMeta();
        if (meta == constants_1.ACK) {
            this.writeAvailable = true;
            this.emit('writeAvailable');
        }
        else if (meta == constants_1.CLOSING) {
            this.__close();
        }
        else if (meta == constants_1.NAME_CONN) {
            this.name = message.getData();
            this.emit('name');
        }
        if (message.getAckrequired()) {
            this.__ack();
        }
    };
    Transport.prototype.__ack = function () {
        this.__writeMeta(constants_1.ACK);
    };
    Transport.prototype.__writeMeta = function (meta, data) {
        var message = new socketmessage_1.SocketMessage();
        message.setMeta(meta);
        if (data) {
            message.setData(data);
        }
        this.__sendAll(message, true);
    };
    Transport.prototype.__sendAll = function (message, overrideAck) {
        if ((this.writeAvailable || overrideAck) && this.opened) {
            if (this.requireAck && !overrideAck) {
                message.setAckrequired(true);
            }
            if (message.getAckrequired() == true) {
                this.writeAvailable = false;
            }
            var toSend = message.serializeBinary();
            if (this.useCompression) {
                throw new Error('Not implemented');
            }
            this.socket.write(toSend + DELIMITER);
            return void 0;
        }
        if (!this.bufferEnabled && message.getMeta() != constants_1.CLOSING) {
            throw new Error('Unable to write; port locked or not opened');
        }
        this.waitingBuffer.push(message);
    };
    Transport.prototype.__close = function () {
        this.opened = false;
        this.socket.destroy();
    };
    return Transport;
}(events_1.EventEmitter));
exports.Transport = Transport;
