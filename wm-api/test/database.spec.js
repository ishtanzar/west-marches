import {DatabaseService} from "../src/database.mjs";
import {beforeEach, expect} from "@jest/globals";
import {ANY} from "lmdb-query";

describe('Database testing', () => {
    let db_svc, users_db;

    beforeEach(() => {
        db_svc = new DatabaseService({
            lmdb: {
                root: "/opt/project/wm-infra/deploy/local/data/api/westmarches.db",
                schema: "westmarches",
            }
        });

        users_db = db_svc.open('users.mdb')
    })

    test('it should list users', async () => {
        let users = users_db.find();

        expect(users).toHaveLength(1);

        let {value: user} = users[0];
        expect(user).toHaveProperty('discord.id')
    });

    test('it should search user', async () => {
        // let users = users_db.find({discord: {id: (value) => value === '323793120787693569' ? value : undefined}});
        let users = users_db.find({discord: {id: '323793120787693569'}});
        expect(users).toHaveLength(1);
    });

});