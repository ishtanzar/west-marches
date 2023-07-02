import winston from "winston";
import {ElasticsearchTransport} from "winston-elasticsearch";

export default class ActorAuditPlugin {

    /**
     *
     * @param {ExtensibleFoundryPlugin} base
     */
    constructor(base) {
        this.auditLogger = winston.createLogger({
            transports: [
                new ElasticsearchTransport({
                    clientOpts: {
                      node: 'http://elasticsearch:9200'
                    },
                    indexPrefix: 'foundry_audit',
                    indexSuffixPattern: 'YYYY.MM'
                })
            ]
        });

        base.hooks.on('pre.actor._onUpdate', this._onUpdate.bind(this));
        base.hooks.on('audit.user.login', this.userLogin.bind(this));
    }

    async _onUpdate(actor, changed, options, user) {
        this.auditLogger.info(`Actor modified`, {actor: actor.id, changes: changed, user: user.id});
    }

    userLogin(req, session, user) {
        this.auditLogger.info(`User login`, {req: {ip: req.ip}, session: session.id, user: {id: user.id, name: user.name}});
    }

}