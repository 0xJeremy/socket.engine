'use strict'

var assertion = require('assert');
var hub = require('../hub');

var DEBUG = false;
var DELAY = 1000;
var TIMEOUT = 0.5;
var CHANNEL = 'Test';

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

function failure(text) {
	console.log('\x1b[31m[%s]\x1b[0m', text);
}

function initialize(port=8080) {
	var h1 = new hub(8080)
	var h2 = new hub(8081)
	h1.connect(CHANNEL, "127.0.0.1", h2.port)
	report("Hubs created and started")
	return [h1, h2]
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


//////////////////
/// UNIT TESTS ///
//////////////////

function test_hub_connection_setup() {
	var h1 = new hub(8080);
	assert(h1.opened, true);
	assert(h1.stopped, false);
	var h2 = new hub(8081);
	assert(h2.opened, true);
	assert(h2.stopped, false);
	report("Sockets opened and started");
	assert(h1.connections.length, 0);
	assert(h2.connections.length, 0);
	assert(h1.address_connections.length, 0);
	assert(h2.address_connections.length, 0);
	report("Connection assertions finished");
	h1.close();
	h2.close();
	assert(h1.stopped, true);
	assert(h1.opened, false);
	assert(h2.stopped, true);
	assert(h2.opened, false);
	success("Hub Connection Setup Test Passed");
}

function test_connection_setup() {
	var h1 = new hub(8082);
	var h2 = new hub(8083);
	h2.on('connection', (data) => {
		assert(h1.connections.length, 1);
		assert(h2.connections.length, 1);
		var c1 = h1.connections[0];
		var c2 = h2.connections[0];
		assert(c1.opened, true);
		assert(c2.opened, true);
		assert(c1.stopped, false);
		assert(c2.stopped, false);
		c2.on("verify", (data) => {
			assert(c1.name, CHANNEL);
			assert(c2.name, CHANNEL);
			h1.close();
			h2.close();
			success("Connection Setup Test Passed");
		})
		assert(c1.addr, '127.0.0.1');
		assert(c2.addr, '127.0.0.1');
		c1.write("verify", "verify");
	})
	h1.connect(CHANNEL, '127.0.0.1', h2.port);
}

function test_empty_messages() {
	var h1 = new hub(8084);
	var h2 = new hub(8085);
	assert(h1.get_all("Test"), []);
	assert(h2.get_all("Test"), []);
	assert(h1.get_all("Test2"), []);
	assert(h2.get_all("Test2"), []);
	h2.on("connection", (data) => {
		assert(h1.get_all("Test"), []);
		assert(h2.get_all("Test"), []);
		assert(h1.get_all("Test2"), []);
		assert(h2.get_all("Test2"), []);
		h1.close();
		h2.close();
		success("Empty messsages Test Passed");
	})
	h1.connect("Test", "127.0.0.1", h2.port);
}

function test_oneway_messages() {
	var h1 = new hub(8086);
	var h2 = new hub(8087);
	assert(h1.get_all("Test"), []);
	assert(h2.get_all("Test"), []);
	assert(h1.get_all("Test2"), []);
	assert(h2.get_all("Test2"), []);
	h2.on("Test", (data) => {
		assert(h1.get_all("Test"), []);
		assert(h2.get_all("Test"), ["test of port 1"]);
		assert(h1.get_all("Test2"), []);
		assert(h2.get_all("Test2"), []);
		h1.write_to_name("Test", "Test2", "test of port 2");
	})
	h2.on("Test2", (data) => {
		assert(h1.get_all("Test"), []);
		assert(h2.get_all("Test"), ["test of port 1"]);
		assert(h1.get_all("Test2"), []);
		assert(h2.get_all("Test2"), ["test of port 2"]);
		h1.close();
		h2.close();
		success("One-way messages Test Passed");
	})
	h2.on("connection", (data) => {
		h1.write_to_name("Test", "Test", "test of port 1");
	})
	h1.connect("Test", "127.0.0.1", h2.port);
}

function test_bidirectional_messages() {
	var h1 = new hub(8088);
	var h2 = new hub(8089);
	assert(h1.get_all("Test"), []);
	assert(h2.get_all("Test"), []);
	assert(h1.get_all("Test2"), []);
	assert(h2.get_all("Test2"), []);
	var tests_run = 0;
	var num_tests = 4;
	function verify() {
		tests_run += 1;
		if(tests_run == num_tests) {
			h1.close();
			h2.close();
			success("Bidirectional messages Test Passed")
		}
	}
	h1.on("Test", (data) => {
		assert(h1.get_all("Test"), ["test of port 1"]);
		verify();
	})
	h1.on("Test2", (data) => {
		assert(h1.get_all("Test2"), ["test of port 2"]);
		verify();
	})
	h2.on("Test", (data) => {
		assert(h2.get_all("Test"), ["test of port 1"]);
		verify();
	})
	h2.on("Test2", (data) => {
		assert(h2.get_all("Test2"), ["test of port 2"]);
		verify();
	})
	h1.connect("Test", "127.0.0.1", h2.port);
	setTimeout(() => {
		h1.write_to_name("Test", "Test", "test of port 1");
		h1.write_to_name("Test", "Test2", "test of port 2");
		h2.write_to_name("Test", "Test", "test of port 1");
		h2.write_to_name("Test", "Test2", "test of port 2");
	}, DELAY)
}

function test_high_speed_messages_oneway() {
	var h1 = new hub(8090);
	var h2 = new hub(8091);
	h1.connect("Test", "127.0.0.1", h2.port);
	var num_runs = 5000;
	h2.on("finally", (data) => {
		var flag = true;
		for(var i = 0; i < num_runs; i++) {
			if(verify([h2.get_all("Test"+i)], ["test of port "+i]) == false) {
				flag = false;
			}
		}
		h1.close();
		h2.close()
		if(flag) {
			success("High Speed One-Way Hub Test Passed");
		} else {
			failure("High Speed One-Way Hub Test Failed");
		}
	})
	setTimeout(() => {
		for(var i = 0; i < num_runs; i++) {
			h1.write_all("Test"+i, "test of port "+i);
		}
		h1.write_all("finally", 'true');
	}, DELAY)
}

function test_high_speed_messages_bidirectional() {
	var h1 = new hub(8092);
	var h2 = new hub(8093);
	h1.connect("Test", "127.0.0.1", h2.port);
	var num_runs = 1000;
	h2.on("finally", (data) => {
		var flag = true;
		for(var i = 0; i < num_runs; i++) {
			if(verify([h1.get_all("Test"+i)], ["test of port "+i]) == false ||
			   verify([h2.get_all("Test"+i)], ["test of port "+i]) == false) {
				flag = false;
			}
		}
		h1.close();
		h2.close()
		if(flag) {
			success("High Speed Bidirectional Hub Test Passed");
		} else {
			failure("High Speed Bidirectional Hub Test Failed");
		}
	})
	setTimeout(() => {
		for(var i = 0; i < num_runs; i++) {
			h1.write_all("Test"+i, "test of port "+i);
		}
		setTimeout(() => {
			for(var i = 0; i < num_runs; i++) {
				h2.write_all("Test"+i, "test of port "+i);
			}
			h1.write_all("finally", 'true');
		}, DELAY)
	}, DELAY)
}

function test_high_throughput_messages_oneway() {
	var h1 = new hub(8094);
	var h2 = new hub(8095);
	h1.connect("Test", "127.0.0.1", h2.port);
	var num_runs = 5000;
	h2.on("finally", (data) => {
		var flag = true;
		for(var i = 0; i < num_runs; i++) {
			if(verify([h2.get_all("Test"+i)], [text]) == false) {
				flag = false;
				console.log(i)
			}
		}
		h1.close();
		h2.close()
		if(flag) {
			success("High Throughput One-way Hub Test Passed");
		} else {
			failure("High Throughput One-way Hub Test Failed");
		}
	})
	setTimeout(() => {
		for(var i = 0; i < num_runs; i++) {
			h1.write_all("Test"+i, text);
		}
		h1.write_all("finally", 'true');
	}, DELAY)
}

function test_high_throughput_messages_bidirectional() {
	var h1 = new hub(8096);
	var h2 = new hub(8097);
	h1.connect("Test", "127.0.0.1", h2.port);
	var num_runs = 50;
	h2.on("finally", (data) => {
		var flag = true;
		for(var i = 0; i < num_runs; i++) {
			if(verify([h2.get_all("Test"+i)], [text]) == false) {
				flag = false;
				console.log(i)
			}
		}
		h1.close();
		h2.close()
		if(flag) {
			success("High Throughput Bidirectional Hub Test Passed");
		} else {
			failure("High Throughput Bidirectional Hub Test Failed");
		}
	})
	setTimeout(() => {
		for(var i = 0; i < num_runs; i++) {
			h1.write_all("Test"+i, text);
		}
		setTimeout(() => {
			for(var i = 0; i < num_runs; i++) {
				h2.write_all("Test"+i, text);
			}
			h1.write_all("finally", 'true');
		}, DELAY)
	}, DELAY)
}


function main() {
	var routines = [test_hub_connection_setup, test_connection_setup, test_empty_messages,
					test_oneway_messages, test_bidirectional_messages, test_high_speed_messages_oneway,
					test_high_speed_messages_bidirectional, test_high_throughput_messages_oneway, 
					test_high_throughput_messages_bidirectional];
	for(var i = 0; i < routines.length; i++) {
		routines[i]();
	}
}
main();
