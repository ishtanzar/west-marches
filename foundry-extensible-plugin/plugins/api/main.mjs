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
      router.search('/api/actors', foundryActors.search);
      router.search('/api/users', foundryUsers.search);
      router.post('/api/users', foundryUsers.create);
      router.put('/api/users/:userId', foundryUsers.update);
      router.get('/api/activity', foundryActivity.get);
    });

    base.hooks.on('pre.express.userSessionMiddleware', (req, resp, next) => {
      if(req.path.startsWith('/api')) {
        next();
        return false;
      }
      return true;
    });
  }
}
