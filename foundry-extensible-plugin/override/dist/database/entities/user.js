'use strict';

const {paths} = global;

const User = require(paths.code + '/database/entities/user');

class ExtensibleUser extends User {

  static get name() {
    return super.name;
  }

  static get schema() {
    const schema = super.schema;

    const {extensibleFoundry} = global;
    extensibleFoundry.hooks.call('post.user.schema', schema);

    return schema;
  }

  static async getUsers() {
    const {game} = global;
    const CONST = require(paths.code + '/const');

    const users = await this.find({});
    this.updateActivity(users);

    users.sort((user1, user2) => {
      let role1 = user1.role >= CONST.USER_ROLES['ASSISTANT'] ? user1['role'] : 1;
      let role2 = user2['role'] >= CONST.USER_ROLES['ASSISTANT'] ? user2.role : 1;
      if (role1 !== role2) return role2 - role1;
      return user1.name.localeCompare(user2.name);
    });

    return game.users = users;
  }

  static updateActivity(users) {
    const {game} = global;
    const connectedUsers = game.activity.users;

    for (let user of users) {
      if (!user['_id']) continue;
      const connected = connectedUsers[user['_id']] || {};
      user['active'] = connected['active'] || false;
      user['sceneId'] = connected['sceneId'] || null;
    }
  }

}

exports.default = ExtensibleUser;
module.exports = ExtensibleUser;
