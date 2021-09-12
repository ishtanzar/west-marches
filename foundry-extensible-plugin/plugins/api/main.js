'use strict';

const Actors = require('./actors');
const Users = require('./users');

class ApiPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    const foundryActors = new Actors();
    const foundryUsers = new Users();

    base.hooks.on('pre.express.defineRoutes', router => {
      router.get('/api/actors', foundryActors.get);
      router.get('/api/users', foundryUsers.get);
      router.post('/api/users', foundryUsers.create);
      router.put('/api/users/:userId', foundryUsers.update);
    });
  }
}

module.exports = ApiPlugin;