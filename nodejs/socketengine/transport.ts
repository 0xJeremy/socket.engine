import { EventEmitter } from 'events';
import { TextEncoder } from 'util';
import { Socket } from 'net';
import { SocketMessage } from './socketmessage';
import { ACK, IMAGE, CLOSING, NAME_CONN } from './constants';

const DELIMITER = '\0\0\0';

export class Transport extends EventEmitter {

  private name?: string;
  private readonly channels: Map<string, any> = new Map<string, any>();
  private writeAvailable: boolean = true;
  private foundDelimiter: boolean = false;
  private opened: boolean = false;
  private socket!: Socket;
  private addr?: string;
  private port?: number;
  private msgBuffer: string = '';
  private readonly waitingBuffer: SocketMessage[] = [];

  public constructor(private readonly useCompression: boolean, private readonly requireAck: boolean, private readonly bufferEnabled: boolean) {
    super();
    this.name = undefined;
    this.addr = undefined;
    this.port = undefined;
  }

   public connect(name: string, addr: string, port: number): void {
    this.name = name;
    this.addr = addr;
    this.port = port;
    while (true) {
      try {
        this.socket.connect(this.port, this.addr, () => {
          this.emit('connected');
        });
        break;
      } catch (err) {
        console.log(err);
      }
    }
    this.opened = true;
    this.__start();
    this.__writeMeta(NAME_CONN, this.name);
  }

  public receive(socket: Socket, addr: string, port: number): void {
    this.socket = socket;
    this.addr = addr;
    this.port = port;
    return this.__start();
  }

  public get(channel: string): unknown {
    return this.channels.get(channel);
  }

  public getImg(): unknown {
    return this.channels.get(IMAGE);
  }

  public write(channel: string, data: string): void {
    const message = new SocketMessage();
    message.setType(channel);
    message.setData(data);
    this.__sendAll(message);
  }

  public writeImage(data: string): void {
    const message = new SocketMessage();
    message.setType(IMAGE);
    message.setData(data);
    this.__sendAll(message);
  }

  public close(): void {
    try {
      this.__writeMeta(CLOSING);
    } catch {}
    this.__close();
  }

  private __start(): void {
    return this.__run();
  }

  private __run(): void {
    this.opened = true;
    this.foundDelimiter = false;

    if (!this.socket) {
      throw new Error('Unable to start Transport; socket does not exist.');
    }

    this.socket.on('data', (bytes: Uint8Array) => {
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

  private __sendWaitingMessages(): void {
    for (let i = 0; i < this.waitingBuffer.length; i++) {
      const message = this.waitingBuffer.shift();
      if (message) {
        this.__sendAll(message);
      }
    }
  }

  private __processMessage(): void {
    const messages = this.msgBuffer.split(DELIMITER);
    if (this.useCompression) {
      // TODO: pull in zlib compression
      throw new Error('Not implemented.');
    }
    for (let i = 0; i < messages.length; i++) {
      // TODO: Make this more efficient
      const encoder = new TextEncoder();
      const message = SocketMessage.deserializeBinary(encoder.encode(messages[i]));

      if (message.getType() == IMAGE) {
        // this.channels.set(IMAGE, decodeImg(message.data));
        this.channels.set(IMAGE, message.getData());
      } else if (message.getData() != '') {
        this.channels.set(message.getType(), message.getData());
      }

      this.__cascade(message);
      messages[i] = '';
    }
    this.msgBuffer = messages.join('');
  }

  private __cascade(message: SocketMessage): void {
    const meta = message.getMeta();
    if (meta == ACK) {
      this.writeAvailable = true;
      this.emit('writeAvailable');
    } else if (meta == CLOSING) {
      this.__close();
    } else if (meta == NAME_CONN) {
      this.name = message.getData();
      this.emit('name');
    }
    if (message.getAckrequired()) {
      this.__ack();
    }
  }

  private __ack(): void {
    this.__writeMeta(ACK);
  }

  private __writeMeta(meta: string, data?: string): void {
    const message = new SocketMessage();
    message.setMeta(meta);
    if(data) {
      message.setData(data);
    }
    this.__sendAll(message, true);
  }

  private __sendAll(message: SocketMessage, overrideAck?: boolean): void {
    if ((this.writeAvailable || overrideAck) && this.opened) {
      if (this.requireAck && !overrideAck) {
        message.setAckrequired(true);
      }
      if (message.getAckrequired() == true) {
        this.writeAvailable = false;
      }
      const toSend = message.serializeBinary()
      if (this.useCompression) {
        throw new Error('Not implemented');
      }
      this.socket.write(toSend + DELIMITER);

      return void 0;
    }
    if (!this.bufferEnabled && message.getMeta() != CLOSING) {
      throw new Error('Unable to write; port locked or not opened');
    }
    this.waitingBuffer.push(message);
  }

  private __close(): void {
    this.opened = false;
    this.socket.destroy();
  }

}
