import BaseActor from 'foundry:dist/database/documents/actor.mjs';

export default class Actor extends BaseActor {

    async _preUpdate(changed, options, user) {
        await extensibleFoundry.hooks.callAsync('pre.actor._preUpdate', this, changed, options, user);
        return super._preUpdate(changed, options, user);
    }

}