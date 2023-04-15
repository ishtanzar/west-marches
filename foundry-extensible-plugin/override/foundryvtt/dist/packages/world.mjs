import World from 'foundry:dist/packages/world.mjs';

export default class ExtensibleWorld extends World {

  async setup() {
    await super.setup();
    await extensibleFoundry.hooks.callAsync('post.world.setup');
  }

  async updateActivePacks() {
    await extensibleFoundry.hooks.callAsync('pre.world.updateActivePacks');
    await super.updateActivePacks();
    await extensibleFoundry.hooks.callAsync('post.world.updateActivePacks');
  }

  get modules() {
    const modules = super.modules;
    extensibleFoundry.hooks.call('post.world.modules', modules);
    return modules;
  }

  static async vend(userId) {
    const {config, db, demo, game, release, logger} = global, world = game.world;
    const user = game.users.find((user => user.id === userId));

    if (!user) throw new Error(`The requested user ID ${userId} does not exist`);

    const worldObject = {
      userId: userId,
      release: release,
      world: game.world.toObject(),
      system: game.world.system,
      modules: game.world.modules,
      paused: game.paused,
      demo: demo,
      addresses: config.express.getInvitationLinks(),
      files: config.files.clientConfig,
      options: {
        language: config.options.language,
        port: config.options.port,
        routePrefix: config.options.routePrefix,
        updateChannel: config.options.updateChannel,
        demo: null !== config.options.demo,
        debug: config.options.debug
      },
      activeUsers: Array.from(Object.keys(game.activity.users))
    };
    worldObject.world.id = game.world.id;

    const seeAll = user.hasRole('ASSISTANT');

    const promises = [];
    // promises.push(db.User.dump().then((e => worldObject.users = e)))
    promises.push(db.User.find().then((e => worldObject.users = e.map(u => {
      if(seeAll || u.id === userId) {
        delete u.password;
        delete u.passwordSalt;
        return u;
      } else {
        return {
          _id: u.id,
          avatar: u.avatar,
          color: u.color,
          name: u.name,
          role: u.role
        };
      }
    }))));

    // promises.push(db.Actor.dump({sort: "name"}).then((e => worldObject.actors = e)))
    promises.push(seeAll ?
      db.Actor.dump({sort: "name"}).then((e => worldObject.actors = e)) :
      db.Actor.find({}, {sort: "name"}).then((e => worldObject.actors = e
        .filter(a => a.testUserPermission(user, "OBSERVER"))
        .map(a => a.toObject()))));

    // promises.push(db.Cards.dump({sort: "name"}).then((e => worldObject.cards = e)))
    promises.push(seeAll ?
      db.Cards.dump({sort: "name"}).then((e => worldObject.cards = e)) :
      db.Cards.find({}, {sort: "name"}).then((e => worldObject.cards = e
        .filter(a => a.testUserPermission(user, "OBSERVER"))
        .map(a => a.toObject()))));

    // promises.push(db.Item.dump({sort: "name"}).then((e => worldObject.items = e)))
    promises.push(seeAll ?
      db.Item.dump({sort: "name"}).then((e => worldObject.items = e)) :
      db.Item.find({}, {sort: "name"}).then((e => worldObject.items = e
        .filter(a => a.testUserPermission(user, "OBSERVER"))
        .map(a => a.toObject()))));

    // promises.push(db.Macro.dump().then((e => worldObject.macros = e)))
    promises.push(seeAll ?
      db.Macro.dump().then((e => worldObject.macros = e)) :
      db.Macro.find({}).then((e => worldObject.macros = e
        .filter(a => a.testUserPermission(user, "OBSERVER"))
        .map(a => a.toObject()))));

    // promises.push(db.RollTable.dump({sort: "name"}).then((e => worldObject.tables = e)))
    promises.push(seeAll ?
      db.RollTable.dump().then((e => worldObject.tables = e)) :
      db.RollTable.find({}).then((e => worldObject.tables = e
        .filter(a => a.testUserPermission(user, "OBSERVER"))
        .map(a => a.toObject()))));

    // promises.push(db.JournalEntry.dump().then((e => worldObject.journal = e)))
    promises.push(seeAll ?
      db.JournalEntry.dump().then((e => worldObject.journal = e)) :
      db.JournalEntry.find({}).then((e => worldObject.journal = e
        .filter(a => a.testUserPermission(user, "OBSERVER"))
        .map(a => a.toObject()))));


    promises.push(db.ChatMessage.dump({sort: "timestamp"}).then((e => worldObject.messages = e)))
    promises.push(db.Combat.dump().then((e => worldObject.combats = e)))
    promises.push(db.Folder.dump({sort: "name"}).then((e => worldObject.folders = e)))
    promises.push(db.Playlist.dump({sort: "name"}).then((e => worldObject.playlists = e)))
    promises.push(db.Scene.dump({sort: "name"}).then((e => worldObject.scenes = e)))
    promises.push(db.Setting.dump().then((e => worldObject.settings = e)))
    promises.push(config.updater.checkCoreUpdateAvailability().then((e => worldObject.coreUpdate = e)))
    promises.push(worldObject.system.getUpdateNotification().then((e => worldObject.systemUpdate = e)))

    const moduleConfig = await global.db.Setting.getValue("core.moduleConfiguration") || {};
    for (let mod of worldObject.modules) mod.active = moduleConfig[mod.data.name] || false;

    // worldObject.packs = world.getActivePacks(moduleConfig);
    worldObject.packs = world.getActivePacks(moduleConfig).filter(p => seeAll || (p.private !== false));
    for (let pack of worldObject.packs) {
      const t = db.packs.get(`${pack.package}.${pack.name}`);
      t && promises.push(t.getIndex().then((t => pack.index = t)))
    }

    await Promise.all(promises)

    return worldObject
  }

}

