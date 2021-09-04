'use strict';

const {paths} = global;

const {World} = require(paths.code + '/packages/world');

class ExtensibleWorld extends World {

  constructor(options) {
    super(options);

    const {extensibleFoundry} = global;
    extensibleFoundry.hooks.call('post.world.constructor', this);
  }

  async setup() {
    await super.setup();

    const {extensibleFoundry} = global;
    extensibleFoundry.hooks.call('post.world.setup', this);
  }

}

module.exports = {'World': ExtensibleWorld};
