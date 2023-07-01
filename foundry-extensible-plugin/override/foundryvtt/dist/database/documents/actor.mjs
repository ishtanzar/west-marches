import BaseActor from 'foundry:dist/database/documents/actor.mjs';

export default class Actor extends BaseActor {

    async _preCreate(data, options, user) {
        const params = {
            data: data,
            options: options,
            user: user,
            result: await super._preCreate(data, options, user)
        };
        await extensibleFoundry.hooks.callAsync('post.actor._preCreate', this, params);

        return params.result;
    }

    async _preUpdate(changed, options, user) {
        await extensibleFoundry.hooks.callAsync('pre.actor._preUpdate', this, changed, options, user);
        return super._preUpdate(changed, options, user);
    }

}