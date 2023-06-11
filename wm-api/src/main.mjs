import {App} from "./app.mjs";
import http from "http";
import {Server} from "socket.io";
import path from "path";
import {fileURLToPath} from "url";
import _ from 'lodash';
import Honeycomb from "honeycomb-grid";
import {registerWindow, SVG} from "@svgdotjs/svg.js";
import {createSVGWindow} from "svgdom";
import dayjs from "dayjs";

String.prototype.format = function () {
    // store arguments in an array
    const args = arguments;
    // use replace to iterate over the string
    // select the match and check if the related argument is present
    // if yes, replace the match with the argument
    return this.replace(/{([a-zA-Z0-9_]+)}/g, function (match, index) {
        // check if the argument is present
        if(typeof args[0] == 'object' && args[0].hasOwnProperty(index)) {
            return args[0][index];
        } else if(typeof args[index] !== 'undefined') {
            return args[index];
        }
        return match;
    });
};

dayjs.locale('fr');

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const { default: config } = await import(path.relative(__dirname, process.env.CONFIG_PATH), { assert: { type: "json" } })

if('DISCORD_OAUTH_CLIENT' in process.env) {
    config.oauth.discord.client_id = process.env.DISCORD_OAUTH_CLIENT;
}

if('DISCORD_OAUTH_SECRET' in process.env) {
    config.oauth.discord.client_secret = process.env.DISCORD_OAUTH_SECRET;
}

if('KANKA_OAUTH_CLIENT' in process.env) {
    config.oauth.kanka.client_id = process.env.KANKA_OAUTH_CLIENT;
}

if('KANKA_OAUTH_SECRET' in process.env) {
    config.oauth.kanka.client_secret = process.env.KANKA_OAUTH_SECRET;
}

if('JWT_SHARED_KEY' in process.env) {
    config.jwt = _.merge({
        shared_key: process.env.JWT_SHARED_KEY
    }, config.jwt);
}

config.web = _.merge({
    host: process.env.WEB_ROOT,
    admin_key: process.env.ADMIN_KEY
}, config.web)

const app = global.app = new App(config);

await app.initialize();

const server = http.createServer(app.get);
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
