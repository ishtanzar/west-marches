import {app} from "./app.mjs";
import http from "http";
import {Server} from "socket.io";

const server = http.createServer(app);
const io = new Server(server);
const port = 3000;

io.on('connection', (socket) => {
    console.log('Connection from ' + socket.handshake.address)
    //TODO: abuseipdb check

    socket.on('addlocation_map', (data) => {
        console.log('test')
    })

    socket.on('location_focus', (data) => {
        console.log('Focus on location: ' + data);
    })
});

console.log('Starting server on port ' + port);
server.listen(port);
