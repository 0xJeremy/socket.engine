'use strict';

const assertion = require('assert');
const Host = require('../index').Host;
const Client = require('../index').Client;

const DEBUG = false;
const DELAY = 1000;

// //////////////////////
// / HELPER FUNCTIONS ///
// //////////////////////

function report(text) {
  if (DEBUG) {
    console.log('\x1b[33m[%s]\x1b[0m', text);
  }
}

function success(text) {
  console.log('\x1b[32m[%s]\x1b[0m', text);
}

function failure(text) {
  console.log('\x1b[31m[%s]\x1b[0m', text);
}

function initialize(port = 8080) {
  const h = new Host('127.0.0.1', port);
  const c = new Client('127.0.0.1', port);
  report('Sockets initialized');
  h.start();
  c.start();
  report('Sockets started');
  return [h, c];
}

function assert(v1, v2) {
  assertion.deepEqual(v1, v2);
}

function verify(a1, a2) {
  for (let i = 0; i < a1.length; i++) {
    for (let j = 0; j < a2.length; j++) {
      if (a1[i] != a2[j]) {
        return false;
      }
    }
  }
  if (a1.length != a2.length) {
    return false;
  }
  return true;
}

/* eslint-disable max-len, no-multi-str */

const text =
  'Consulted he eagerness unfeeling deficient existence of. Calling nothing end fertile for venture way boy. Esteem spirit temper too say adieus who direct esteem. It esteems luckily mr or picture placing drawing no. Apartments frequently or motionless on reasonable projecting expression. Way mrs end gave tall walk fact bed. \
Left till here away at to whom past. Feelings laughing at no wondered repeated provided finished. It acceptance thoroughly my advantages everything as. Are projecting inquietude affronting preference saw who. Marry of am do avoid ample as. Old disposal followed she ignorant desirous two has. Called played entire roused though for one too. He into walk roof made tall cold he. Feelings way likewise addition wandered contempt bed indulged. \
Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate. Longer ladies valley get esteem use led six. Middletons resolution advantages expression themselves partiality so me at. West none hope if sing oh sent tell is. \
Death weeks early had their and folly timed put. Hearted forbade on an village ye in fifteen. Age attended betrayed her man raptures laughter. Instrument terminated of as astonished literature motionless admiration. The affection are determine how performed intention discourse but. On merits on so valley indeed assure of. Has add particular boisterous uncommonly are. Early wrong as so manor match. Him necessary shameless discovery consulted one but. \
Yet remarkably appearance get him his projection. Diverted endeavor bed peculiar men the not desirous. Acuteness abilities ask can offending furnished fulfilled sex. Warrant fifteen exposed ye at mistake. Blush since so in noisy still built up an again. As young ye hopes no he place means. Partiality diminution gay yet entreaties admiration. In mr it he mention perhaps attempt pointed suppose. Unknown ye chamber of warrant of norland arrived. \
Luckily friends do ashamed to do suppose. Tried meant mr smile so. Exquisite behaviour as to middleton perfectly. Chicken no wishing waiting am. Say concerns dwelling graceful six humoured. Whether mr up savings talking an. Active mutual nor father mother exeter change six did all. ';

/* eslint-enable */

// ////////////////
// / UNIT TESTS ///
// ////////////////

function testConnectionBoth() {
  const h = new Host('127.0.0.1');
  assert(h.opened, false);
  h.start();
  assert(h.opened, true);
  const c = new Client('127.0.0.1');
  assert(c.opened, false);
  c.start();
  assert(c.opened, true);
  report('Socket opened and started');
  assert(h.clients.length, 0);
  assert(h.sockets.length, 0);
  c.close();
  h.close();
  success('Connection test Passed');
}

function testConnectionMessageCallback() {
  const sockets = initialize(8081);
  const h = sockets[0];
  const c = sockets[1];
  h.on('connection', (data) => {
    report('Connection callback started');
    assert(data, [true]);
    assert(h.sockets.length, 1);
    assert(h.clients.length, 1);
    report('Connections tested');
    c.close();
    h.close();
    success('Test Message Connection Passed');
  });
  assert(h.clients.length, 0);
  assert(h.sockets.length, 0);
  c.write('connection', true);
  report('Wrote connection');
}

function testEmptyMessage() {
  const sockets = initialize(8082);
  const h = sockets[0];
  const c = sockets[1];
  assert(c.get('Test'), undefined);
  assert(c.get('Test2'), undefined);
  assert(h.get_ALL('Test'), []);
  assert(h.get_ALL('Test2'), []);
  c.close();
  h.close();
  success('Empty messages test Passed');
}

function testHostMessage() {
  const sockets = initialize(8083);
  const h = sockets[0];
  const c = sockets[1];
  assert(h.get_ALL('Test'), []);
  assert(h.get_ALL('Test2'), []);
  let passed = false;
  h.on('Test', (data) => {
    assert(h.get_ALL('Test'), ['test of port 1']);
    if (passed) {
      c.close();
      h.close();
      success('Client -> Host Passed');
    } else {
      passed = true;
    }
  });
  h.on('Test2', (data) => {
    assert(h.get_ALL('Test2'), ['test of port 2']);
    if (passed) {
      c.close();
      h.close();
      success('Client -> Host Passed');
    } else {
      passed = true;
    }
  });
  c.write('Test', 'test of port 1');
  c.write('Test2', 'test of port 2');
  report('Wrote test messages');
}

function testClientMessage() {
  const sockets = initialize(8084);
  const h = sockets[0];
  const c = sockets[1];
  assert(c.get('Test'), undefined);
  assert(c.get('Test2'), undefined);
  let passed = false;
  c.write('connection', true);
  c.on('Test', (data) => {
    assert(c.get('Test'), 'test of port 1');
    if (passed) {
      h.close();
      c.close();
      success('Host -> Client Passed');
    } else {
      passed = true;
    }
  });
  c.on('Test2', (data) => {
    assert(c.get('Test2'), 'test of port 2');
    if (passed) {
      h.close();
      c.close();
      success('Host -> Client Passed');
    } else {
      passed = true;
    }
  });
  setTimeout(() => {
    h.write_ALL('Test', 'test of port 1');
    h.write_ALL('Test2', 'test of port 2');
    report('Wrote test messages');
  }, DELAY);
}

function testBidirectionalMessage() {
  const sockets = initialize(8085);
  const h = sockets[0];
  const c = sockets[1];
  assert(c.get('Test'), undefined);
  assert(c.get('Test2'), undefined);
  assert(h.get_ALL('Test'), []);
  assert(h.get_ALL('Test2'), []);
  const numTests = 3;
  let testsRun = 0;
  const finish = () => {
    h.close();
    c.close();
    success('Host <-> Client Passed');
  };
  c.on('Test', (data) => {
    assert(c.get('Test'), 'test of port 1');
    report('Client test passed');
    if (testsRun == numTests) {
      finish();
    } else {
      testsRun += 1;
    }
  });
  c.on('Test2', (data) => {
    assert(c.get('Test2'), 'test of port 2');
    report('Client test2 passed');
    if (testsRun == numTests) {
      finish();
    } else {
      testsRun += 1;
    }
  });
  h.on('Test', (data) => {
    assert(h.get_ALL('Test'), ['test of port 1']);
    report('Host test passed');
    if (testsRun == numTests) {
      finish();
    } else {
      testsRun += 1;
    }
  });
  h.on('Test2', (data) => {
    assert(h.get_ALL('Test2'), ['test of port 2']);
    report('Host test2 passed');
    if (testsRun == numTests) {
      finish();
    } else {
      testsRun += 1;
    }
  });
  c.write('connection', true);
  setTimeout(() => {
    h.write_ALL('Test', 'test of port 1');
    h.write_ALL('Test2', 'test of port 2');
    c.write('Test', 'test of port 1');
    c.write('Test2', 'test of port 2');
  }, DELAY);
}

function testHighSpeedClient() {
  const sockets = initialize(8086);
  const h = sockets[0];
  const c = sockets[1];
  c.write('connected', true);
  const numRuns = 1000;
  h.on('finally', (data) => {
    let flag = true;
    for (let i = 0; i < numRuns; i++) {
      if (verify(h.get_ALL('Test' + i), ['test of port ' + i]) == false) {
        flag = false;
      }
    }
    h.close();
    c.close();
    if (flag) {
      success('High Speed Client -> Host Passed');
    } else {
      failure('High Speed Client -> Host Failed');
    }
  });
  for (let i = 0; i < numRuns; i++) {
    c.write('Test' + i, 'test of port ' + i);
  }
  c.write('finally', true);
}

function testHighSpeedHost() {
  const sockets = initialize(8087);
  const h = sockets[0];
  const c = sockets[1];
  c.write('connected', true);
  const numRuns = 1000;
  c.on('finally', (data) => {
    let flag = true;
    for (let i = 0; i < numRuns; i++) {
      if (verify([c.get('Test' + i)], ['test of port ' + i]) == false) {
        flag = false;
      }
    }
    h.close();
    c.close();
    if (flag) {
      success('High Speed Host -> Client Passed');
    } else {
      failure('High Speed Host -> Client Failed');
    }
  });
  setTimeout(() => {
    for (let i = 0; i < numRuns; i++) {
      h.write_ALL('Test' + i, 'test of port ' + i);
    }
    h.write_ALL('finally', true);
  }, DELAY);
}

function testHighThroughputClient() {
  const sockets = initialize(8088);
  const h = sockets[0];
  const c = sockets[1];
  c.write('connected', true);
  const numRuns = 2000;
  h.on('finally', (data) => {
    let flag = true;
    for (let i = 0; i < numRuns; i++) {
      if (verify(h.get_ALL('Test' + i), [text]) == false) {
        flag = false;
      }
    }
    h.close();
    c.close();
    if (flag) {
      success('High Throughput Client -> Host Passed');
    } else {
      failure('High Throughput Client -> Host Failed');
    }
  });
  for (let i = 0; i < numRuns; i++) {
    c.write('Test' + i, text);
  }
  c.write('finally', true);
}

function testHighThroughputHost() {
  const sockets = initialize(8089);
  const h = sockets[0];
  const c = sockets[1];
  c.write('connected', true);
  const numRuns = 2000;
  c.on('finally', (data) => {
    let flag = true;
    for (let i = 0; i < numRuns; i++) {
      if (verify([c.get('Test' + i)], [text]) == false) {
        flag = false;
      }
    }
    h.close();
    c.close();
    if (flag) {
      success('High Throughput Host -> Client Passed');
    } else {
      failure('High Throughput Host -> Client Failed');
    }
  });
  setTimeout(() => {
    for (let i = 0; i < numRuns; i++) {
      h.write_ALL('Test' + i, text);
    }
    h.write_ALL('finally', true);
  }, DELAY);
}

function main() {
  const routines = [
    testConnectionBoth,
    testConnectionMessageCallback,
    testEmptyMessage,
    testHostMessage,
    testClientMessage,
    testBidirectionalMessage,
    testHighSpeedClient,
    testHighSpeedHost,
    testHighThroughputClient,
    testHighThroughputHost,
  ];
  for (let i = 0; i < routines.length; i++) {
    routines[i]();
  }
}
main();
