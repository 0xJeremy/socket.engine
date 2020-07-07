"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Transport = void 0;
const events_1 = require("events");
const util_1 = require("util");
const socketmessage_1 = require("./socketmessage");
const constants_1 = require("./constants");
const DELIMITER = '\0\0\0';
class Transport extends events_1.EventEmitter {
    constructor(useCompression, requireAck, bufferEnabled) {
        super();
        this.useCompression = useCompression;
        this.requireAck = requireAck;
        this.bufferEnabled = bufferEnabled;
        this.channels = new Map();
        this.writeAvailable = true;
        this.foundDelimiter = false;
        this.opened = false;
        this.msgBuffer = '';
        this.waitingBuffer = [];
        this.name = undefined;
        this.addr = undefined;
        this.port = undefined;
    }
    connect(name, addr, port) {
        this.name = name;
        this.addr = addr;
        this.port = port;
        while (true) {
            try {
                this.socket.connect(this.port, this.addr, () => {
                    this.emit('connected');
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
    }
    receive(socket, addr, port) {
        this.socket = socket;
        this.addr = addr;
        this.port = port;
        return this.__start();
    }
    get(channel) {
        return this.channels.get(channel);
    }
    getImg() {
        return this.channels.get(constants_1.IMAGE);
    }
    write(channel, data) {
        const message = new socketmessage_1.SocketMessage();
        message.setType(channel);
        message.setData(data);
        this.__sendAll(message);
    }
    writeImage(data) {
        const message = new socketmessage_1.SocketMessage();
        message.setType(constants_1.IMAGE);
        message.setData(data);
        this.__sendAll(message);
    }
    close() {
        try {
            this.__writeMeta(constants_1.CLOSING);
        }
        catch { }
        this.__close();
    }
    __start() {
        return this.__run();
    }
    __run() {
        this.opened = true;
        this.foundDelimiter = false;
        if (!this.socket) {
            throw new Error('Unable to start Transport; socket does not exist.');
        }
        this.socket.on('data', (bytes) => {
            const read = bytes.toString();
            // TODO: add last bit of buffer here
            if (read.includes(DELIMITER)) {
                this.foundDelimiter = true;
            }
            this.msgBuffer += read.toString();
            if (this.msgBuffer != '' && this.foundDelimiter) {
                this.__processMessage();
                this.foundDelimiter = false;
            }
            this.__sendWaitingMessages();
        });
        this.socket.on('end', () => {
            this.emit('end');
        });
        this.socket.on('error', (err) => {
            this.emit('warning', err);
        });
    }
    __sendWaitingMessages() {
        for (let i = 0; i < this.waitingBuffer.length; i++) {
            const message = this.waitingBuffer.shift();
            if (message) {
                this.__sendAll(message);
            }
        }
    }
    __processMessage() {
        const messages = this.msgBuffer.split(DELIMITER);
        if (this.useCompression) {
            // TODO: pull in zlib compression
            throw new Error('Not implemented.');
        }
        for (let i = 0; i < messages.length; i++) {
            // TODO: Make this more efficient
            const encoder = new util_1.TextEncoder();
            const message = socketmessage_1.SocketMessage.deserializeBinary(encoder.encode(messages[i]));
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
    }
    __cascade(message) {
        const meta = message.getMeta();
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
    }
    __ack() {
        this.__writeMeta(constants_1.ACK);
    }
    __writeMeta(meta, data) {
        const message = new socketmessage_1.SocketMessage();
        message.setMeta(meta);
        if (data) {
            message.setData(data);
        }
        this.__sendAll(message, true);
    }
    __sendAll(message, overrideAck) {
        if ((this.writeAvailable || overrideAck) && this.opened) {
            if (this.requireAck && !overrideAck) {
                message.setAckrequired(true);
            }
            if (message.getAckrequired() == true) {
                this.writeAvailable = false;
            }
            const toSend = message.serializeBinary();
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
    }
    __close() {
        this.opened = false;
        this.socket.destroy();
    }
}
exports.Transport = Transport;
