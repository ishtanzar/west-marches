
const { Server } = require("socket.io");

const io = new Server();
const port = 3000;

io.on('connection', (socket) => {
    console.log('Connection from ' + socket.handshake.address)
    //TODO: abuseipdb check
});

console.log('Starting server on port ' + port);
io.listen(port);
