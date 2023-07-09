
import Actor from 'foundry:dist/database/documents/actor.mjs';

export default class Actors {
  async search(req, resp) {
    try {
      const defaultFilter = {'type': 'character'};
      const vars = {
        req: req,
        resp: resp,
        filter: req.body || defaultFilter,
        actors: []
      };

      resp.set('Content-Type', 'application/json');

      await extensibleFoundry.hooks.callAsync('pre.api.actors.search', vars);
      vars.actors = await Actor.find(Object.keys(vars.filter).length > 0 ? vars.filter : defaultFilter);
      await extensibleFoundry.hooks.callAsync('post.api.actors.search', vars);

      resp.send(JSON.stringify({ actors: vars.actors }));
    } catch (ex) {
      resp.status(500).end(ex.toString());
    }
  }
}
