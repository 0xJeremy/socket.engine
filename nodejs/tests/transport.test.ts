import { expect } from "chai";
import { DeferPromise } from "./helpers";
import { Transport } from "../socketengine";

const ADDRESS = '127.0.0.1';
const PORT = 8080;

describe("Transport Interface Test", function () {
  it("Should close synchronously", function () {
    const transport = new Transport();
    expect(transport.isOpen()).to.be.false;
    transport.close();
    expect(transport.isOpen()).to.be.false;
  });

  it("Should form a connection", async function () {
    const finished = DeferPromise();
    const receiver = new Transport();
    receiver.openForConnection(PORT);
    const remote = new Transport();
    remote.connect(ADDRESS, PORT);

    receiver.on("opened", () => {
      expect(receiver.isOpen()).to.be.true;
      expect(remote.isOpen()).to.be.true;
      receiver.close();
      remote.close();
      expect(receiver.isOpen()).to.be.false;
      expect(remote.isOpen()).to.be.false;

      finished.resolve();
    });

    await finished.promise;
  });

  it("Should not contain any messages", async function () {
    const finished = DeferPromise();
    const receiver = new Transport();
    receiver.openForConnection(PORT);
    const remote = new Transport();
    remote.connect(ADDRESS, PORT);

    receiver.on("opened", () => {
      expect(receiver.get("test")).to.be.undefined;
      expect(remote.get("test")).to.be.undefined;
      receiver.close();
      remote.close();

      finished.resolve();
    });

    await finished.promise;
  });

  it("Should assign a name (remote -> local)", async function () {
    const finished = DeferPromise();
    const receiver = new Transport();
    receiver.openForConnection(PORT);
    const remote = new Transport();
    remote.connect(ADDRESS, PORT);

    receiver.on("name", (name) => {
      expect(name).to.equal("test");
      expect(remote.getName()).to.equal("test");
      remote.close();

      finished.resolve();
    });

    receiver.on("opened", () => {
      remote.assignName("test");
    });

    await finished.promise;
  });

  it("Should assign a name (local -> remote)", async function () {
    const finished = DeferPromise();
    const receiver = new Transport();
    receiver.openForConnection(PORT);
    const remote = new Transport();
    remote.connect(ADDRESS, PORT);

    remote.on("name", (name) => {
      expect(name).to.equal("test");
      expect(receiver.getName()).to.equal("test");
      receiver.close();

      finished.resolve();
    });

    receiver.on("opened", () => {
      receiver.assignName("test");
    });

    await finished.promise;
  });

  it('Should write and emit', async function() {
    const finished = DeferPromise();
    const receiver = new Transport();
    receiver.openForConnection(PORT);
    const remote = new Transport();
    remote.connect(ADDRESS, PORT);
    const testString = 'Hello World!';
    const testChannel = 'testChannel';

    remote.on(testChannel, (data) => {
      expect(data).to.equal(testString);
      expect(remote.get(testChannel)).to.equal(testString);
      remote.close();

      finished.resolve();
    });

    receiver.on(testChannel, (data) => {
      expect(data).to.equal(testString);
      expect(receiver.get(testChannel)).to.equal(testString);
      receiver.write(testChannel, testString);
    });

    receiver.on('opened', () => {
      remote.write(testChannel, testString);
    });

    await finished.promise;
  });

  it('Should write and emit with ack', async function(this) {
    const finished = DeferPromise();
    const receiver = new Transport({ requireAck: true });
    receiver.openForConnection(PORT);
    const remote = new Transport({ requireAck: true });
    remote.connect(ADDRESS, PORT);
    const testString = 'Hello World!';
    const testChannel = 'testChannel';

    remote.on(testChannel, (data) => {
      expect(data).to.equal(testString);
      expect(remote.get(testChannel)).to.equal(testString);
      receiver.close();

      finished.resolve();
    });

    receiver.on(testChannel, (data) => {
      expect(data).to.equal(testString);
      expect(receiver.get(testChannel)).to.equal(testString);
    });

    remote.on('writeAvailable', () => {
      receiver.write(testChannel, testString);
    })

    receiver.on('opened', () => {
      remote.write(testChannel, testString);
    });

    await finished.promise;
  });
});
