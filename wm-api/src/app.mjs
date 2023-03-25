import express from 'express';
import proxy from 'express-http-proxy';
import path from 'path';
import cors from 'cors';
import Ajv from 'ajv';
import {fileURLToPath} from 'url';
import {readFile} from "fs/promises";

import sharp from 'sharp';
import { open } from 'lmdb';
import {Client, EmbedBuilder, TextChannel} from "discord.js";

import _ from 'lodash';
import Honeycomb from 'honeycomb-grid';
import {registerWindow, SVG} from '@svgdotjs/svg.js';
import {createSVGWindow} from 'svgdom';
import schema_hex from './schema_hex.mjs';
import {verifyKeyMiddleware, InteractionResponseType} from "discord-interactions";
import crypto from "crypto";
import {readFileSync, writeFileSync} from "fs";
import dayjs from "dayjs";
import 'dayjs/locale/fr.js';
import BeeQueue from "bee-queue";
import {KofiDonationProcessor} from "./kofi.mjs";

String.prototype.format = function () {
    // store arguments in an array
    const args = arguments;
    // use replace to iterate over the string
    // select the match and check if the related argument is present
    // if yes, replace the match with the argument
    return this.replace(/{([0-9]+)}/g, function (match, index) {
        // check if the argument is present
        return typeof args[index] == 'undefined' ? match : args[index];
    });
};


global._ = _;
global.Honeycomb = Honeycomb;
global.SVG = SVG;
global.window = createSVGWindow()

registerWindow(window, window.document);
dayjs.locale('fr');

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const { hexMapConfig } = await import(path.relative(__dirname, process.env.HEXMAP_CONFIG));
const { HexmapFactory } = await import(path.relative(__dirname, '/opt/hexmap/hexmap.mjs'));
const { default: config } = await import(path.relative(__dirname, process.env.CONFIG_PATH), { assert: { type: "json" } })
config.kofi.verification_token = process.env.KOFI_VERIFICATION

const ajv = new Ajv();
export const app = express();

const discord = new Client({intents: []});

const validate_body_hex = ajv.compile(schema_hex)
const hexMap = new HexmapFactory(hexMapConfig.default);
const map800 = hexMap.build(hexMapConfig.map800);
const map12 = hexMap.build(hexMapConfig.map12);

const kofiPayloads = new BeeQueue('kofi_payloads', {
    redis: {
        host: 'redis'
    }
});

kofiPayloads.on('job succeeded', async (jobId, _) => {
   await kofiPayloads.removeJob(jobId);
});

let ioSocket;

await discord.login(process.env.DISCORD_BOT_SECRET);

app.use(cors());
app.set('etag', true);
app.use('/kanka_api', proxy('kanka.io', {
    https: true,
    proxyReqPathResolver: function (req) {
        return '/api' + req.url
    }
}));

const processor = new KofiDonationProcessor(config, discord);
kofiPayloads.process(job => processor.process_kofi_payload(job.data));

/**
 *
 * @param {number} zoom
 * @returns {lmdb.Database<any, lmdb.Key>}
 */
function getZoomDB(zoom) {
    return open({
        path: `/opt/project/wm-infra/deploy/local/data/api/westmarches.db/westmarches/map-${zoom}-data.mdb`,
        maxDbs: 1
    }).openDB('documents', {});
}

const chartedMapFile = process.env.FINAL_MAP;

async function buildChartedMap() {
    const db = getZoomDB(0);
    db.getRange()
        .filter(({ key, value }) => value.charted === true)
        .forEach(({ key, value }) => {
            const point = map12.hexGridFactory(map12.hexFactory([value.x, value.y]))[0].toPoint()
            map12.svgGroup.use(map12.baseSymbol)
                .translate(point.x + map12.options.offset.x, point.y + map12.options.offset.y)
                .stroke('none')
                .fill('white')
        })

    try {
        const alpha = sharp(Buffer.from(map12.svg.node.outerHTML))
            .extractChannel('alpha')

        const hexRaw = await sharp(await readFile(process.env.BASE_MAP))
            .joinChannel(await alpha.toBuffer())
            .png({palette: true, compressionLevel: 0})
            .toBuffer()

        // const tilePng = await sharp(hexRaw)
        //     .extract({
        //         left: Math.round(point.x + map12.options.offset.x),
        //         top: Math.round(point.y + map12.options.offset.y),
        //         width: Math.round(map12.options.hexSize * 2),
        //         height: Math.round(map12.options.hexSize * Math.sqrt(3))})
        //     .toBuffer()

        await sharp(await readFile(process.env.FOW_PATH))
            .composite([
                { input: hexRaw },
            ])
            .jpeg({quality: 100})
            .toFile(chartedMapFile);
    } catch (e) {
        console.log(e);
    }
}

/**
 *
 * @param {string} param
 * @returns {string[]}
 */
function validate_param_zoom(param) {
    return param.match(/^[0-9]$/)
}

app.get('/health', async (req, res) => {
    res.send('OK')
})

app.get('/map/:zoom/charted.json', async (req, res) => {
    if(validate_param_zoom(req.params.zoom)) {
        const db = getZoomDB(req.params.zoom)

        res.json({
            'charted': db.getRange().map(entry => entry.value)
        })
    } else {
        res.status(400).json({message: "Bad Request"})
    }
})

app.post('/map/:zoom/charted.json', express.json(), async (req, res) => {
    if(validate_param_zoom(req.params.zoom) && validate_body_hex(req.body)) {
        const hexmap = req.body.hexmap || [req.body],
            db = getZoomDB(req.params.zoom),
            ops = []

        db.getRange().forEach(({ key, value }) => {
            let index;
            const hex = hexmap.filter((hex, idx) => {
                if(hex.x === key[0] && hex.y === key[1]) {
                    index = idx; return true
                }
            })
            if(hex.length > 0) {
                ops.push(db.put(key, _.merge(value, hex[0])))
                hexmap.splice(index, 1);
            }
        })

        hexmap.forEach(hex => ops.push(db.put([hex.x, hex.y], hex)))

        await Promise.all(ops)
        await buildChartedMap();

        res.status(200).json({message: "OK"})
    } else {
        res.status(400).json({message: "Bad Request"})
    }
})

app.get('/map/:zoom/charted.jpg', async (req, res) => {
    // 800/1019-389.png Aberdeen
    // 12/90-25.png Aberdeeen

    // res.type('.jpg')
    // res.set('etag', crypto.createHmac('sha256', finalBuffer).digest('base64'))
    res.sendFile(chartedMapFile)
});

app.get('/donations/progress.jpg', async (req, resp) => {
    resp.sendFile('/opt/project/wm-api/src/progress.jpg');
})

app.post('/discord/interactions', verifyKeyMiddleware(process.env.DISCORD_BOT_PUBLIC_KEY), async (req, res) => {
    switch (req.body.data?.custom_id) {
        case 'generic_cancel':
            /**
             * @type {TextChannel}
             */
            const channel = await discord.channels.fetch(req.body.message.channel_id);
            await channel.messages.delete(req.body.message.id);
            break;
        case 'map_set_location':
            res.json({
                type: InteractionResponseType.DEFERRED_UPDATE_MESSAGE,
                data: {}
            })
            break;
        case 'map_fly_to':
            break;
        default:

    }
});

app.post('/kofi/hook', express.urlencoded({ extended: true}), async (req, resp) => {
    if(req.body.data) {
        await kofiPayloads.createJob(JSON.parse(req.body.data)).save();
        resp.send('OK');
    } else {
        resp.status(400).send('KO')
    }
});
