
import Actor from 'foundry:dist/database/documents/actor.mjs';

export default class Actors {
  async get(req, resp) {
    try {
      const vars = {
        req: req,
        resp: resp,
        filter: req.query,
        actors: []
      };

      await extensibleFoundry.hooks.callAsync('pre.api.actors.get', vars);

      resp.set('Content-Type', 'application/json');

      vars.actors = await Actor.find(Object.keys(vars.filter).length > 0 ? vars.filter : {'type': 'character'});

      await extensibleFoundry.hooks.callAsync('post.api.actors.get', vars);

      resp.send({ actors: vars.actors });
    } catch (ex) {
      resp.status(500).end(ex.toString());
    }
  }
}
