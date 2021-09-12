'use strict';

const User = require('../../override/dist/user');

class Users {

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
        let user = await User.findOne({ name: name });
        if(user) {
          resp.send({'user_id': user._id});
        } else {
          const user_data = {name: name, role: role ? role : 1};
          extensibleFoundry.hooks.call('pre.api.user.create', req, resp, user_data);

          user = User.create(user_data);
          await user.save();

          resp.send({'user_id': user._id});
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
        const user = await User.findOne({ _id: userId });
        if(user) {
          user.name = req.body.name || user.name;
          user.role = req.body.role || user.role;
          user.save();

          resp.send({
            'id': user._id,
            'name': user.name,
            'role': user.role
          })
        }
      } else {
        resp.sendStatus(400);
      }
    } catch (ex) {
      resp.status(500).send(ex.toString());
    }
  }
}

module.exports = Users;