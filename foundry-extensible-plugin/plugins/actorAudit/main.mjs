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
                    indexSuffixPattern: 'YYYY.MM',
                    indexTemplate: {
                        "priority": 200,
                        "template": {
                            "settings": {
                                "index": {
                                    "mapping": {
                                        "total_fields": {
                                            "limit": "3000"
                                        }
                                    },
                                    "refresh_interval": "5s",
                                    "number_of_shards": "1",
                                    "number_of_replicas": "0"
                                }
                            },
                            "mappings": {
                                "_source": {
                                    "enabled": true
                                },
                                "properties": {
                                    "severity": {
                                        "index": true,
                                        "type": "keyword"
                                    },
                                    "source": {
                                        "index": true,
                                        "type": "keyword"
                                    },
                                    "@timestamp": {
                                        "type": "date"
                                    },
                                    "@version": {
                                        "type": "keyword"
                                    },
                                    "fields": {
                                        "dynamic": true,
                                        "type": "object"
                                    },
                                    "message": {
                                        "index": true,
                                        "type": "text"
                                    }
                                }
                            }
                        },
                        "index_patterns": [
                            "foundry_audit*"
                        ]
                    }
                })
            ]
        });

        base.hooks.on('pre.actor._onUpdate', this._onUpdate.bind(this));
        base.hooks.on('audit.user.login', this.userLogin.bind(this));
    }

    async _onUpdate(actor, changed, options, user) {
        this.auditLogger.info(`Actor modified`, {actor: actor.id, changes: changed, user: {id: user.id, name: user.name}});
    }

    userLogin(req, session, user) {
        this.auditLogger.info(`User login`, {req: {ip: req.ip}, session: session.id, user: {id: user.id, name: user.name}});
    }

}