'use strict'

var	base64 = new RegExp('^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$');

var decodeImg = function(img) {
	if(base64.test(img)) {
		return img;
	}
	return null;
}

module.exports.decodeImg = decodeImg;
