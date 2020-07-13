"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isValidImage = void 0;
const base64 = new RegExp(
  "^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"
);
function isValidImage(image) {
  return base64.test(image);
}
exports.isValidImage = isValidImage;
