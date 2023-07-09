import fs from "fs";
import path from "path";
import {fileURLToPath} from "url";
import Users from "../users.mjs";
import Actors from "../actors.mjs";
import Activity from "../activity.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function mockResponse() {
    const spy = jasmine.createSpyObj('resp', ['send', 'set', 'status'], {statusCode: 200});
    spy.status.and.returnValue(jasmine.createSpyObj(['end']));
    return spy;
}

describe('Activity endpoint', () => {
    afterAll(() => {
        game.activity.users = {}
    })

    it('should show online', async () => {
        const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'user.json')));
        game.activity.users[data._id] = 'xyz';

        const apiActivity = new Activity();

        spyOn(db.User, 'get').and.returnValue(Promise.resolve(db.User._create(data)))
        const resp = mockResponse();

        await apiActivity.get({}, resp);

        expect(resp.statusCode).toEqual(200);
        expect(resp.send).toHaveBeenCalledWith({
            users: [data.name]
        });
    })
})

describe('Actors endpoint', () => {
    const apiActors = new Actors();

    it('should list actors', async () => {
        const char_type = "vehicule";
        const str_json = fs.readFileSync(path.join(__dirname, 'actor.json'));

        spyOn(db.Actor, 'find').and.returnValue(Promise.resolve([db.Actor._create(JSON.parse(str_json))]));

        const resp = mockResponse();

        await apiActors.search({
            body: { type: char_type }
        }, resp);

        expect(db.Actor.find).toHaveBeenCalledOnceWith({type: char_type});
        expect(resp.statusCode).toEqual(200);
        expect(resp.send).toHaveBeenCalledWith(JSON.stringify({
            actors: [db.Actor._create(JSON.parse(str_json)).toJSON()]
        }));
    })
})

describe('Users endpoint', () => {
    const json_data = fs.readFileSync(path.join(__dirname, 'user.json'));
    const data = JSON.parse(json_data);

    const apiUsers = new Users();

    beforeEach(() => {
        const user = db.User._create(JSON.parse(json_data));

        spyOn(db.User, 'get').and.returnValue(user)
        spyOn(db.User, 'find').and.returnValue([user])
        spyOn(db.User, 'create').and.returnValue(Promise.resolve(user));
        spyOn(user, 'update').and.returnValue(user)
    })

    it('should find users', async () => {
        const name = 'toto';
        const resp = mockResponse();

        await apiUsers.search({
            query: { name: name }
        }, resp);

        expect(resp.statusCode).toEqual(200);
        expect(resp.send).toHaveBeenCalledWith(JSON.stringify({
            users: [JSON.parse(json_data)]
        }));
    });

    it('should create users', async () => {
        const resp = mockResponse();

        await apiUsers.create({
            body: {name: data.name}
        }, resp);

        expect(resp.statusCode).toEqual(200);
        expect(resp.send).toHaveBeenCalledWith({
            id: data._id
        });
    });

    it('should update users', async () => {
        const data = JSON.parse(json_data);
        const resp = mockResponse();

        await apiUsers.update({
            params: { userId: data._id },
            body: { role: 1 }
        }, resp);

        expect(resp.statusCode).toEqual(200);
        expect(resp.send).toHaveBeenCalledWith({
            _id: data._id,
            name: data.name,
            role: data.role
        });
    });
})