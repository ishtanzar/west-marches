
export default class WestMarchesBackendPlugin {

    /**
     *
     * @param {ExtensibleFoundryPlugin} base
     */
    constructor(base) {
        base.hooks.on('post.actor._preCreate', this.actorPreCreate.bind(this));
    }

    async actorPreCreate(actor, params) {
        if(params.user.isGM) {
            global.logger.info(`${params.user.name} (${params.user.id}) is GM, removing ownership of created ${actor.name}`)

            delete actor.data.permission[params.user.id];
            delete actor.data._source.permission[params.user.id];
        }
    }
}