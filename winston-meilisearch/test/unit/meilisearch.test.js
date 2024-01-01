const winston = require('winston');
const assert = require('assert');
const MeiliSearchTransport = require("../../index");
const dayjs = require("dayjs");

describe('winston-meilisearch', function () {
    describe('#log()', function () {
        it('should behave correctly', function () {
            const mock_docs = [];
            const user = {
                id: 'user_id',
                name: 'user_name'
            }
            let mock_index;

            const logger = winston.createLogger({
                transports: [
                    new MeiliSearchTransport({
                        client: {
                            index: idx => {
                                mock_index = idx;
                                return {
                                    addDocuments: docs => {
                                        mock_docs.push(docs);
                                    }
                                }
                            }
                        }
                    })
                ]
            });

            logger.info('Actor modified', {actor: 'actor_id', changes: {}, user: {id: user.id, name: user.name}});

            assert.equal(mock_docs.length, 1);
            assert.equal(mock_index, 'logs-' + dayjs().format('YYYY_MM_DD'));
        });
    });
});
