var host = require('./socketengine');

var h = new host().start();

h.on('thing', (data) => {
	console.log("I AM THE INTERFACE: ", data)
})
