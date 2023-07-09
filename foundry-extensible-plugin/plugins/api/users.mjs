'use strict';

import User from 'foundry:dist/database/documents/user.mjs';

export default class Users {

  async search(req, resp) {
    const {extensibleFoundry} = global;
    const vars = {
      req: req,
      resp: resp,
      filter: req.body || {},
      projection: { password: 0, auth: 0 },
      users: []
    };

    await extensibleFoundry.hooks.callAsync('pre.api.user.search', vars);
    vars.users = await User.find(vars.filter, {project: vars.projection});
    await extensibleFoundry.hooks.callAsync('post.api.user.search', vars);

    resp.send(JSON.stringify({ users: vars.users }));
  }

  async create(req, resp) {
    const name = req.body.name;
    const role = req.body.role;
    const {extensibleFoundry} = global;

    if(name) {
      try {
        let [user] = await User.find({ name: name });
        if(user) {
          resp.send({id: user.id});
        } else {
          const user_data = {name: name, role: role ? role : 1};
          extensibleFoundry.hooks.call('pre.api.user.create', req, resp, user_data);

          user = await User.create(user_data);
          resp.send({id: user.id});
        }
      } catch (ex) {
        resp.status(500).send(ex.toString());
      }
    } else {
      resp.sendStatus(400);
    }
  }

  async update(req, resp) {
    const userId = req.params.userId;

    try {
      if(userId) {
        let user = await User.get(userId);
        if(user) {
          const update = {
            '_id': userId,
            name: req.body.name || user.name,
            role: req.body.role || user.role
          };

          if(req.body.password) {
            update.password = req.body.password;
          }

          if(req.body.discord) {
            update.discord = req.body.discord
            ;
          }

          const updated = await user.update(update);

          resp.send(Object.assign({
            '_id': userId,
            'name': updated.name,
            'role': updated.role
          }));
        }
      } else {
        resp.sendStatus(400);
      }
    } catch (ex) {
      resp.status(500).send(ex.toString());
    }
  }
}
