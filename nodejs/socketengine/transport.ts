import { EventEmitter } from "events";
import { Socket, createServer } from "net";
import { SocketMessage } from "./socketmessage";

/////////////////
/// CONSTANTS ///
/////////////////

import { ACK, IMAGE, CLOSING, NAME_CONN } from "./constants";
import { isValidImage } from "./common";

const DELIMITER_STRING = "\0\0\0";
const DELIMITER_BUFFER = Buffer.from([0, 0, 0]);
const DELIMITER_LENGTH = DELIMITER_STRING.length;

interface ITransportOptions {
  useCompression?: boolean;
  requireAck?: boolean;
  bufferEnabled?: boolean;
}

///////////////////////////////////////////////////////////////

///////////////////////
/// TRANSPORT CLASS ///
///////////////////////

export class Transport extends EventEmitter {
  private name?: string;
  private readonly channels: Map<string, any> = new Map<string, any>();
  private readonly useCompression: boolean = false;
  private readonly requireAck: boolean = false;
  private readonly bufferEnabled: boolean = false;
  private writeAvailable: boolean = true;
  private foundDelimiter: boolean = false;
  private opened: boolean = false;
  private socket!: Socket;
  private addr?: string;
  private port?: number;
  private msgBuffer: string = "";
  private readonly waitingBuffer: SocketMessage[] = [];

  public constructor(options?: ITransportOptions) {
    super();
    this.name = undefined;
    this.addr = undefined;
    this.port = undefined;
    if (!options) {
      return;
    }
    if (options.useCompression) {
      this.useCompression = options.useCompression;
    }
    if(options.requireAck) {
      this.requireAck = options.requireAck;
    }
    if(options.bufferEnabled) {
      this.bufferEnabled = options.bufferEnabled;
    }
  }

  /////////////////
  /// INTERFACE ///
  /////////////////

  public connect(addr: string, port: number): void {
    this.addr = addr;
    this.port = port;
    this.socket = new Socket();
    while (true) {
      try {
        this.socket.connect(this.port, this.addr, () => {
          this.emit("connected");
        });
        break;
      } catch (err) {
        console.log(err);
      }
    }
    this.opened = true;
    this.__start();
  }

  public assignName(name: string): void {
    this.name = name;
    this.__writeMeta(NAME_CONN, this.name);
  }

  public openForConnection(port: number): void {
    const server = createServer();
    server.listen(port, "127.0.0.1");
    server.on("connection", (socket) => {
      server.close();
      server.removeAllListeners();
      this.receive(socket, socket.localAddress, socket.localPort);
    });
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

  public getName(): string | undefined {
    return this.name;
  }

  public getImage(): unknown {
    return this.channels.get(IMAGE);
  }

  public isOpen(): boolean {
    return this.opened;
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
    } catch (err) {
      console.log(err);
    }
    this.__close();
  }

  ///////////////////////
  /// PRIVATE METHODS ///
  ///////////////////////

  private __start(): void {
    return this.__run();
  }

  private __run(): void {
    this.opened = true;
    this.foundDelimiter = false;

    if (!this.socket) {
      throw new Error("Unable to start Transport; socket does not exist.");
    }

    this.socket.on("data", (bytes: Buffer) => {
      let read = bytes.toString();
      if (
        (
          this.msgBuffer.substr(this.msgBuffer.length - DELIMITER_LENGTH) + read
        ).indexOf(DELIMITER_STRING) !== -1
      ) {
        this.foundDelimiter = true;
      }
      this.msgBuffer += read;

      if (this.msgBuffer.length != 0 && this.foundDelimiter) {
        this.__processMessage();
        this.foundDelimiter = false;
      }

      this.__sendWaitingMessages();
    });

    this.socket.on("end", () => {
      this.emit("end");
    });

    this.socket.on("error", (err) => {
      this.emit("warning", err);
    });

    this.emit("opened");
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
    const messages = this.msgBuffer.split(DELIMITER_STRING);
    if (this.useCompression) {
      // TODO: pull in zlib compression
      throw new Error("Not implemented.");
    }
    for (let i = 0; i < messages.length; i++) {
      const message = SocketMessage.deserializeBinary(
        Buffer.from(messages[i])
      ).toObject();
      if (message.type == IMAGE) {
        if (isValidImage(message.meta)) {
          this.channels.set(IMAGE, message.data);
        } else {
          throw new Error("Image invalid base64!");
        }
      } else if (message.data != "") {
        this.channels.set(message.type, message.data);
        this.emit(message.type, message.data);
      }

      this.__cascade(message);
      messages[i] = "";
    }
    this.msgBuffer = messages.join("");
  }

  private __cascade(message: SocketMessage.AsObject): void {
    const meta = message.meta;
    if (meta == ACK) {
      this.writeAvailable = true;
      this.emit("writeAvailable");
    } else if (meta == CLOSING) {
      this.__close();
    } else if (meta == NAME_CONN) {
      this.name = message.data;
      this.emit("name", this.name);
    }
    if (message.ackrequired) {
      this.__ack();
    }
  }

  private __ack(): void {
    this.__writeMeta(ACK);
  }

  private __writeMeta(meta: string, data?: string): void {
    const message = new SocketMessage();
    message.setMeta(meta);
    if (data) {
      message.setData(data);
    }
    this.__sendAll(message, true);
  }

  private __sendAll(message: SocketMessage, overrideAck?: boolean): void {
    if ((this.writeAvailable || overrideAck) && this.opened) {
      if (this.requireAck && overrideAck !== true) {
        message.setAckrequired(true);
      }
      if (message.getAckrequired() == true) {
        this.writeAvailable = false;
      }
      const toSend = Buffer.from(message.serializeBinary());
      if (this.useCompression) {
        throw new Error("Not implemented");
      }

      this.socket.write(toSend);
      this.socket.write(DELIMITER_BUFFER);

      return void 0;
    }
    if (!this.bufferEnabled && message.getMeta() != CLOSING) {
      throw new Error("Unable to write; port locked or not opened");
    }
    this.waitingBuffer.push(message);
  }

  private __close(): void {
    this.opened = false;
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.destroy();
    }
  }
}
