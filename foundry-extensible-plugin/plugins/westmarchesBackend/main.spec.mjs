import WestMarchesBackendPlugin from "./main.mjs";
import Actor from 'foundry:dist/database/documents/actor.mjs';
import User from 'foundry:dist/database/documents/user.mjs';

describe('WestMarchesBackend Plugin', () => {

    it('should remove GM ownership on actor creation', () => {
        const extensiblePluginBase = {
            hooks: jasmine.createSpyObj('extensiblePluginBase', ['on'])
        };

        const plugin = new WestMarchesBackendPlugin(extensiblePluginBase);
        const userId = "xyz123"
        const user = new User({
            id: userId,
            name: "MyUser",
            role: 3
        });

        spyOnProperty(user, 'id').and.returnValue(userId);

        const data = {
            name: "Test",
            type: "character",
            permission: {default: 0},
        }

        const actor = new Actor(data);
        actor.data.permission[userId] = data.permission[userId] = 3;

        expect(user.isGM).toBeTrue();

        plugin.actorPreCreate(actor, {data: data, user: user});

        let expected = {};
        expected[userId] = 3;

        expect(actor.testUserPermission(user, 3, {exact: true})).toBeFalse();
    })

})