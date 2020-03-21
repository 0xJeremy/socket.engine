'use strict'

var assertion = require('assert');
var host = require('../socketengine').host;
var client = require('../socketengine').client;

var DEBUG = false;
var DELAY = 1000;

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

function initialize(port=8080) {
	var h = new host('127.0.0.1', port);
	var c = new client('127.0.0.1', port);
	report("Sockets initialized");
	h.start();
	c.start();
	report("Sockets started")
	return [h, c]
}

function assert(v1, v2) {
	assertion.deepEqual(v1, v2);
}

var text = "Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor match. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. "


//////////////////
/// UNIT TESTS ///
//////////////////

function test_connection_BOTH() {
	var h = new host('127.0.0.1');
	assert(h.opened, false);
	h.start();
	assert(h.opened, true);
	var c = new client('127.0.0.1');
	assert(c.opened, false);
	c.start();
	assert(c.opened, true);
	report("Socket opened and started");
	assert(h.clients.length, 0);
	assert(h.sockets.length, 0);
	c.close();
	h.close();
	success("Connection test Passed");
}

function test_connection_msg_CALLBACK() {
	var sockets = initialize(8081);
	var h = sockets[0];
	var c = sockets[1];
	h.on('connection', (data) => {
		report("Connection callback started")
		assert(data, [true]);
		assert(h.sockets.length, 1);
		assert(h.clients.length, 1);
		report('Connections tested');
		c.close();
		h.close();
		success("Test Message Connection Passed");
	});
	assert(h.clients.length, 0);
	assert(h.sockets.length, 0);
	c.write('connection', true);
	report("Wrote connection");
}

// THIS TEST CURRENTLY FAILS
// MORE DEVELOPMENT NEEDED HERE
// function test_async_ordering() {
// 	var c = new client('127.0.0.1');
// 	c.start()
// 	var h = new host('127.0.0.1');
// 	h.start()
// 	h.on('connection', (data) => {
// 		assert(data, [true]);
// 		assert(h.sockets.length, 1);
// 		assert(h.clients.length, 1);
// 		report('Connections tested');
// 		h.close();
// 		c.close();
// 		success("Async Ordering test Passed");
// 	});
// 	assert(h.clients.length, 0);
// 	assert(h.sockets.length, 0);
// 	c.write('connection', true);
// }

function test_empty_message() {
	var sockets = initialize(8082);
	var h = sockets[0];
	var c = sockets[1];
	assert(c.get("Test"), undefined);
	assert(c.get("Test2"), undefined);
	assert(h.get_ALL("Test"), []);
	assert(h.get_ALL("Test2"), []);
	c.close();
	h.close();
	success("Empty messages test Passed");
}

function test_host_messages() {
	var sockets = initialize(8083);
	var h = sockets[0];
	var c = sockets[1];
	assert(h.get_ALL("Test"), []);
	assert(h.get_ALL("Test2"), []);
	var passed = false;
	h.on("Test", (data) => {
		assert(h.get_ALL("Test"), ["test of port 1"]);
		if(passed) {
			c.close();
			h.close();
			success("Client -> Host Passed");
		} else {
			passed = true;
		}
	});
	h.on("Test2", (data) => {
		assert(h.get_ALL("Test2"), ["test of port 2"]);
		if(passed) {
			c.close();
			h.close();
			success("Client -> Host Passed");
		} else {
			passed = true;
		}
	});
	c.write("Test", "test of port 1");
	c.write("Test2", "test of port 2");
	report("Wrote test messages");
}

function test_client_messages() {
	var sockets = initialize(8084);
	var h = sockets[0];
	var c = sockets[1];
	assert(c.get("Test"), undefined);
	assert(c.get("Test2"), undefined);
	var passed = false;
	c.write("connection", true)
	c.on("Test", (data) => {
		assert(c.get("Test"), "test of port 1");
		if(passed) {
			h.close();
			c.close();
			success("Host -> Client Passed");
		} else {
			passed = true;
		}
	});
	c.on("Test2", (data) => {
		assert(c.get("Test2"), "test of port 2");
		if(passed) {
			h.close();
			c.close();
			success("Host -> Client Passed");
		} else {
			passed = true;
		}
	});
	setTimeout(() => {
		h.write_ALL("Test", "test of port 1");
		h.write_ALL("Test2", "test of port 2");
		report("Wrote test messages");
	}, DELAY);
}

function test_bidirectional_messages() {
	var sockets = initialize(8085);
	var h = sockets[0];
	var c = sockets[1];
	assert(c.get("Test"), undefined);
	assert(c.get("Test2"), undefined);
	assert(h.get_ALL("Test"), []);
	assert(h.get_ALL("Test2"), []);
	var num_tests = 3;
	var tests_run = 0;
	var finish = () => {
		h.close();
		c.close();
		success("Host <-> Client Passed");
	}
	c.on("Test", (data) => {
		assert(c.get("Test"), "test of port 1");
		report("Client test passed");
		if(tests_run == num_tests) {
			finish();
		} else {
			tests_run += 1;
		}
	});
	c.on("Test2", (data) => {
		assert(c.get("Test2"), "test of port 2");
		report("Client test2 passed");
		if(tests_run == num_tests) {
			finish();
		} else {
			tests_run += 1;
		}
	});
	h.on("Test", (data) => {
		assert(h.get_ALL("Test"), ["test of port 1"]);
		report("Host test passed");
		if(tests_run == num_tests) {
			finish();
		} else {
			tests_run += 1;
		}
	});
	h.on("Test2", (data) => {
		assert(h.get_ALL("Test2"), ["test of port 2"]);
		report("Host test2 passed");
		if(tests_run == num_tests) {
			finish();
		} else {
			tests_run += 1;
		}
	});
	c.write("connection", true);
	setTimeout(() => {
		h.write_ALL("Test", "test of port 1");
		h.write_ALL("Test2", "test of port 2");
		c.write("Test", "test of port 1");
		c.write("Test2", "test of port 2");
	}, DELAY)	
}

function main() {
	var routines = [test_connection_BOTH, test_connection_msg_CALLBACK,
					test_empty_message, test_host_messages, test_client_messages,
					test_bidirectional_messages]
	for(var i = 0; i < routines.length; i++) {
		routines[i]();
	}
}
main();
