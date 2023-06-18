//import {beforeEach, expect, jest, test} from '@jest/globals';
//import * as primitives from '../../../app/common/utils/primitives.mjs';
import {noGlobals} from 'jasmine-core';
import crypto from "crypto";
import util from "util";

const {describe, it, expect, afterEach, beforeEach} =  noGlobals();

describe('Actor _preUpdate', () => {
    let actor, creator;

    beforeEach(async () => {
        const {db} = global;

        creator = await db.User.get('YHOrrkO2MJmpyNjm');

        [actor] = await db.DatabaseBackend.create(db.Actor, {
            "data": [{
                "name": "Jasmine Test",
                "type": "character",
            }]
        }, creator);

    });

    afterEach(async () => {
        await actor.delete();
    });

    it('should log updates', async () => {
        // async function countActors() {
        //     return await new Promise((resolve, reject) => {
        //         db.Actor.db.count({}, (err, count) => resolve(count))
        //     });
        // }
        const {db} = global;

        expect(actor.data.data.currency.gp).toEqual(0);
        await db.DatabaseBackend.update(db.Actor, {
            updates: [
                {
                    _id: actor.id,
                    data: {
                        currency: {
                            gp: 30
                        }
                    }
                }
            ]
        }, creator);

        let [updated] = await db.Actor.find({_id: actor.id});

        expect(updated.data.data.currency.gp).toEqual(30);
    })
})