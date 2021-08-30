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

}

exports.default = ExtensibleUser;
module.exports = ExtensibleUser;