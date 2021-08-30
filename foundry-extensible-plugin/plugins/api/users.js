'use strict';


class Users {

  async create(req, resp) {
    const {paths} = global;
    const User = require(paths.code + '/database/entities/user');

    const name = req.body.name;
    const role = req.body.role;

    if(name) {
      try {
        const user = await User.create({name: name, role: role ? role : 1});
        await user.save();
        resp.send({'user_id': user._id});
      } catch (ex) {
        resp.status(500).send(ex.toString());
      }
    } else {
      resp.sendStatus(400);
    }
  }

  async update(req, resp) {
    const {paths} = global;
    const User = require(paths.code + '/database/entities/user');

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