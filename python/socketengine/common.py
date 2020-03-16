import cv2

def encodeImg(img):
	success, encoded_img = cv2.imencode('.png', img)
	return base64.b64encode(encoded_img)
