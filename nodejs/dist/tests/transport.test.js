"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const chai_1 = require("chai");
const socketengine_1 = require("../socketengine");
describe("Sample test", function () {
  it("Should close synchronously", function () {
    const transport = new socketengine_1.Transport();
    transport.close();
    chai_1.expect(transport.isOpen()).to.be.false;
  });
  it("Should form a connection", function () {
    const transport = new socketengine_1.Transport();
    transport.connect("test", "127.0.0.1", 8080);
  });
});
