/// <reference types="node" />
import { EventEmitter } from "events";
import { Socket } from "net";
export declare class Transport extends EventEmitter {
  private readonly useCompression;
  private readonly requireAck;
  private readonly bufferEnabled;
  private name?;
  private readonly channels;
  private writeAvailable;
  private foundDelimiter;
  private opened;
  private socket;
  private addr?;
  private port?;
  private msgBuffer;
  private readonly waitingBuffer;
  constructor(
    useCompression?: boolean,
    requireAck?: boolean,
    bufferEnabled?: boolean
  );
  connect(name: string, addr: string, port: number): void;
  receive(socket: Socket, addr: string, port: number): void;
  get(channel: string): unknown;
  getImg(): unknown;
  isOpen(): boolean;
  write(channel: string, data: string): void;
  writeImage(data: string): void;
  close(): void;
  private __start;
  private __run;
  private __sendWaitingMessages;
  private __processMessage;
  private __cascade;
  private __ack;
  private __writeMeta;
  private __sendAll;
  private __close;
}
