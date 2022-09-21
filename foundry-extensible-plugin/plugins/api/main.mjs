import Actors from "./actors.mjs";
import Users from "./users.mjs";
import Activity from "./activity.mjs";

export default class ApiPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    const foundryActors = new Actors();
    const foundryUsers = new Users();
    const foundryActivity = new Activity();

    base.hooks.on('pre.express.defineRoutes', router => {
      router.get('/api/actors', foundryActors.get);
      router.get('/api/users', foundryUsers.get);
      router.post('/api/users', foundryUsers.create);
      router.put('/api/users/:userId', foundryUsers.update);
      router.get('/api/activity', foundryActivity.get);
    });
  }
}
