// package: 
// file: message.proto

import * as jspb from "google-protobuf";

export class SocketMessage extends jspb.Message {
  getType(): string;
  setType(value: string): void;

  getData(): string;
  setData(value: string): void;

  getMeta(): string;
  setMeta(value: string): void;

  getAckrequired(): boolean;
  setAckrequired(value: boolean): void;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): SocketMessage.AsObject;
  static toObject(includeInstance: boolean, msg: SocketMessage): SocketMessage.AsObject;
  static extensions: {[key: number]: jspb.ExtensionFieldInfo<jspb.Message>};
  static extensionsBinary: {[key: number]: jspb.ExtensionFieldBinaryInfo<jspb.Message>};
  static serializeBinaryToWriter(message: SocketMessage, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): SocketMessage;
  static deserializeBinaryFromReader(message: SocketMessage, reader: jspb.BinaryReader): SocketMessage;
}

export namespace SocketMessage {
  export type AsObject = {
    type: string,
    data: string,
    meta: string,
    ackrequired: boolean,
  }
}

