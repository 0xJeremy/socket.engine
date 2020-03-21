'use strict'

var assertion = require('assert');
var host = require('../socketengine').host;
var client = require('../socketengine').client;

var DEBUG = false;

////////////////////////
/// HELPER FUNCTIONS ///
////////////////////////

function report(text) {
	if(DEBUG) {
		console.log('\x1b[33m[%s]\x1b[0m', text);
	}
}

function success(text) {
	console.log('\x1b[32m[%s]\x1b[0m', text);
}

function initialize() {
	var h = new host('127.0.0.1');
	var c = new client('127.0.0.1');
	report("Sockets initialized");
	h.start();
	c.start();
	report("Sockets started")
	return [h, c]
}

function assert(v1, v2) {
	assertion.deepEqual(v1, v2);
}

function verify(a1, a2) {
	for(var i = 0; i < a1.length; i++) {
		for(var j = 0; j < a2.length; j++) {
			if(a1[i] != a2[j]) {
				return false;
			}
		}
	}
	if(a1.length != a2.length) {
		return false;
	}
	return true;
}

var text = "Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor match. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. "



function test_connection_msg_CALLBACK() {

	var sockets = initialize();
	var h = sockets[0];
	var c = sockets[1]; 

	h.on('connection', (data) => {
		console.log("BEGAN CALLBACK")
		assert(data, [true]);
		assert(h.sockets.length, 1);
		assert(h.clients.length, 1);
		report('Connections tested');
		c.close();
		h.close();
		success("Test Message Connection Passed");
		process.exit();
	});
	
	assert(h.clients.length, 0);
	assert(h.sockets.length, 0);
	
	c.write('connection', true);
	
	
}

test_connection_msg_CALLBACK();