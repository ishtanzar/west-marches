import express from 'express';
import proxy from 'express-http-proxy';
import path from 'path';
import cors from 'cors';
import Ajv from 'ajv';
import {fileURLToPath} from 'url';
import {readFile} from "fs/promises";

import sharp from 'sharp';
import {open} from 'lmdb';
import {Client, TextChannel} from "discord.js";

import _ from 'lodash';
import Honeycomb from 'honeycomb-grid';
import {registerWindow, SVG} from '@svgdotjs/svg.js';
import {createSVGWindow} from 'svgdom';
import schema_hex from './schema_hex.mjs';
import {InteractionResponseType, verifyKeyMiddleware} from "discord-interactions";
import crypto from "crypto";
import dayjs from "dayjs";
import 'dayjs/locale/fr.js';
import BeeQueue from "bee-queue";
import {KofiDonationProcessor} from "./kofi.mjs";
import jwt from "jsonwebtoken";
import {DatabaseService} from "./database.mjs";
import cookieParser from "cookie-parser";
import {oauth_perform, OAuthInvalidCodeException, OAuthInvalidTokenException} from "./auth.mjs";

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

const regex_uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

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

export class App {

    constructor(config) {
        this.config = config;
        this.app = express();
        const db = this.db = new DatabaseService(config)
    }

    get get() {
        return this.app;
    }

    async initialize() {
        await this.middlewares();
        await this.routes();

        return this;
    }

    async middlewares() {
        this.app
            .use(cors())
            .use(express.json())
            .use(cookieParser())
            .use(this.jwt_middleware.bind(this))
            .use('/kanka_api', proxy('kanka.io', {
                https: true,
                proxyReqPathResolver: function (req) {
                    return '/api' + req.urlcookieParser
                }}))
            .set('etag', true);
    }

    async routes() {
        this.app.get('/health', this.health);
        this.app.get('/oauth/:service', this.oauth.bind(this));
        this.app.get('/oauth/discord/perform', this.oauth_discord_perform.bind(this));
        this.app.get('/oauth/kanka/perform',
            (req, res, next) => {
                req.user ? next() : res.status(401).send('Unauthorized')
            },
            this.oauth_kanka_perform.bind(this));
        this.app.post('/kofi/hook', express.urlencoded({ extended: true}), this.kofi);
        this.app.post('/discord/interactions', verifyKeyMiddleware(process.env.DISCORD_BOT_PUBLIC_KEY), this.discord_interactions);

        this.app.get('/users', this.api_key_middleware, this.get_users.bind(this));
        this.app.get('/users/:id', this.api_key_middleware, this.get_user.bind(this));
        this.app.patch('/users/:id', this.api_key_middleware, this.patch_user.bind(this));

        this.app.get('/map/:zoom/charted.json', async (req, res) => {
            if(validate_param_zoom(req.params.zoom)) {
                const db = getZoomDB(req.params.zoom)

                res.json({
                    'charted': db.getRange().map(entry => entry.value)
                })
            } else {
                res.status(400).json({message: "Bad Request"})
            }
        })

        this.app.post('/map/:zoom/charted.json', express.json(), async (req, res) => {
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

        this.app.get('/map/:zoom/charted.jpg', async (req, res) => {
            // 800/1019-389.png Aberdeen
            // 12/90-25.png Aberdeeen

            // res.type('.jpg')
            // res.set('etag', crypto.createHmac('sha256', finalBuffer).digest('base64'))
            res.sendFile(chartedMapFile)
        });

        this.app.get('/donations/progress.jpg', async (req, resp) => {
            resp.sendFile('/opt/project/wm-api/src/progress.jpg');
        })
    }

    async api_key_middleware(req, res, next) {
        let header;
        if ((header = req.header('Authorization')).startsWith('ApiKey-v1')) {
            const [, apiKey] = header.split(' ');
            if (apiKey === config.web.admin_key) {
                return await next();
            }
        }
        res.status(401).send('Unauthorized');
    }

    async jwt_middleware(req, res, next) {
        const {access_token} = req.cookies;

        if(access_token) {
            try {
                const {user_id} = jwt.verify(access_token, this.config.jwt.shared_key);
                req.user = user_id;
            } catch (e) {
                console.warn('Invalid JWT:' + e);
            }
        }

        next();
    }

    async health(req, res) {
        res.send('OK')
    }

    async oauth(req, res) {
        const service = req.params.service;
        const app_redirect = req.query.redirect_uri || null;
        const key = crypto.randomUUID();
        const db = this.db.open(this.config.lmdb.oauth_codes);

        await db.put(key, {
            redirect: app_redirect,
            created_at: Date.now()
        });

        const authorize_url = this.config.oauth[service].endpoint.format({
            client_id: this.config.oauth[service].client_id,
            redirect_uri: `${this.config.web.host}/oauth/${service}/perform`,
            scope: this.config.oauth[service].scopes.join(" "),
            state: key
        });

        res.redirect(authorize_url);
    }

    async oauth_kanka_perform(req, res) {
        const key = req.query.state;
        const code = req.query.code;

        if(req.user && key.match(regex_uuid)) {
            try {
                const oauth = await oauth_perform(
                    this.config.oauth.kanka,
                    code,
                    `${this.config.web.host}/oauth/kanka/perform`
                );

                const oauth_collection = this.db.open(this.config.lmdb.oauth_codes);
                const users_collection = this.db.open(this.config.lmdb.users);

                const redirect = (await oauth_collection.pop(key)).redirect;

                const user = users_collection.get(req.user);

                if(user) {
                    const user_oauth = Object.assign({}, user.oauth, {kanka: oauth.credentials});

                    await users_collection.put(req.user, Object.assign({}, user, {
                        kanka: oauth.identity.data,
                        oauth: user_oauth
                    }));

                    if(redirect) {
                        res.redirect(redirect);
                        return;
                    }
                    res.send('OK');
                }

            } catch (e) {
                console.warn(e);
                if(e instanceof OAuthInvalidCodeException) {
                    res.status(401).send('Could not validate OAuth code');
                } else if(e instanceof OAuthInvalidTokenException){
                    res.status(401).send('Could not fetch resource owner details');
                } else {
                    throw e;
                }
            }

        }
        res.status(401).send('Unauthorized');
    }

    async oauth_discord_perform(req, res) {
        const key = req.query.state;
        const code = req.query.code;

        if(key.match(regex_uuid)) {

            try {
                const oauth = await oauth_perform(this.config.oauth.discord, code, `${this.config.web.host}/oauth/discord/perform`);

                const oauth_collection = this.db.open(this.config.lmdb.oauth_codes);
                const users_collection = this.db.open(this.config.lmdb.users);

                const redirect = (await oauth_collection.pop(key)).redirect;

                const users = users_collection.find({discord: {id: oauth.identity.id}});

                let userId;

                if(users.length >= 1) {
                    [{key: userId}] = users;
                } else {
                    userId = crypto.randomUUID();
                    await users_collection.put(userId, {
                        discord: oauth.identity,
                        oauth: {
                            discord: oauth.credentials
                        }
                    });
                }

                const hostname = new URL(this.config.web.host).hostname;
                const domain = hostname.split('.').slice(1).join('.');
                const token = jwt.sign({ user_id: userId }, config.jwt.shared_key, {
                    expiresIn: '2d',
                    audience: domain,
                    issuer: hostname
                })

                res.cookie('access_token', token, {
                    domain: domain,
                    httpOnly: true,
                    secure: true
                })

                if(redirect) {
                    res.redirect(redirect);
                    return;
                }
                res.send('OK');
            } catch (e) {
                console.warn(e);
                if(e instanceof OAuthInvalidCodeException) {
                    res.status(401).send('Could not validate OAuth code');
                } else if(e instanceof OAuthInvalidTokenException){
                    res.status(401).send('Could not fetch resource owner details');
                } else {
                    throw e;
                }
            }
        } else {
            res.status(401).send('Invalid state');
        }
    }

    async get_users(req,res) {
        const users = this.db.open(this.config.lmdb.users);

        res.json(users.find());
    }

    async get_user(req, res) {
        const userId = req.params.id;

        if(userId.match(regex_uuid)) {
            const users = this.db.open(this.config.lmdb.users);

            res.json(users.get(userId));
        } else {
            res.status(400).send('Invalid ID');
        }
    }

    async patch_user(req, res) {
        const userId = req.params.id;

        if(userId.match(regex_uuid)) {
            const users = this.db.open(this.config.lmdb.users);
            const user = users.get(userId);

            const updated = Object.assign({}, user, req.body);
            await users.put(userId, updated);
            res.json(updated);
        } else {
            res.status(400).send('Invalid ID');
        }
    }

    async discord_interactions(req, res) {
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
    }

    async kofi(req, resp) {
        if(req.body.data) {
            await kofiPayloads.createJob(JSON.parse(req.body.data)).save();
            resp.send('OK');
        } else {
            resp.status(400).send('KO')
        }
    }

}
