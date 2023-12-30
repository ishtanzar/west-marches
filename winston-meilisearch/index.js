const Transport = require('winston-transport');
const defaults = require('lodash.defaults');
const omit = require('lodash.omit');
const dayjs = require('dayjs');
const { MeiliSearch } = require('meilisearch');

module.exports = class MeiliSearchTransport extends Transport {
    constructor(opts) {
        super(opts);
        this.name = 'meilisearch';

        this.opts = opts || {};

        // Set defaults
        defaults(opts, {
            level: 'info',
            index: 'logs-app-default',
            indexPrefix: 'logs',
            indexSuffixPattern: 'YYYY_MM_DD',
            clientOpts: {
                host: 'http://meilisearch:7700'
            }
        });

        this.client = new MeiliSearch(this.opts.clientOpts);
    }

    log(info, callback) {
        const { level, message, timestamp } = info;
        const meta = Object.assign({}, omit(info, ['level', 'message']));
        setImmediate(() => {
            this.emit('logged', info);
        });

        const entry = {
            '@timestamp': timestamp ? timestamp : new Date().toISOString(),
            message: message,
            severity: level,
            fields: meta
        };

        const index = this.client.index(this.getIndexName(this.opts));
        index.addDocuments([entry]);

        // Perform the writing to the remote service
        callback();
    }

    getIndexName(opts) {
        let indexName = opts.index;
        if (indexName === null) {
            // eslint-disable-next-line prefer-destructuring
            let indexPrefix = opts.indexPrefix;
            if (typeof indexPrefix === 'function') {
                // eslint-disable-next-line prefer-destructuring
                indexPrefix = opts.indexPrefix();
            }
            const now = dayjs();
            const dateString = now.format(opts.indexSuffixPattern);
            indexName = indexPrefix
                + '-'
                + dateString;
        }
        return indexName;
    }
};