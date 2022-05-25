'use strict';

import User from 'foundry:dist/database/documents/user.mjs';

export default class Users {

  async get(req, resp) {
    const {extensibleFoundry} = global;
    const vars = {
      req: req,
      resp: resp,
      filter: req.query,
      projection: { password: 0, auth: 0 },
      users: []
    };

    await extensibleFoundry.hooks.callAsync('pre.api.user.get', vars);

    // Foundry's Users.find doesn't consider projections so we need to tap in NeDB API
    vars.users = await new Promise((resolve, reject) => {
      User.db.find(vars.filter, vars.projection).exec((err, docs) => {
        if(err) { reject(err) }
        return resolve(docs);
      });
    })

    await extensibleFoundry.hooks.callAsync('post.api.user.get', vars);

    resp.send({ users: vars.users });
  }

  async create(req, resp) {
    const name = req.body.name;
    const role = req.body.role;
    const {extensibleFoundry} = global;

    if(name) {
      try {
        let [user] = await User.find({ name: name });
        if(user) {
          resp.send({'_id': user._id});
        } else {
          const user_data = {name: name, role: role ? role : 1};
          extensibleFoundry.hooks.call('pre.api.user.create', req, resp, user_data);

          user = User.create(user_data);
          resp.send({'_id': user._id});
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

          const [updated] = await User.database.update(User, {
            updates: [update]
          });

          resp.send(Object.assign({
            '_id': userId,
            'name': user.name,
            'role': user.role
          }, updated));
        }
      } else {
        resp.sendStatus(400);
      }
    } catch (ex) {
      resp.status(500).send(ex.toString());
    }
  }
}
