const base64 = new RegExp(
  "^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"
);

export function isValidImage(image: string): boolean {
  return base64.test(image);
}
