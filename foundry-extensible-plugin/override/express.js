'use strict';

const {paths} = global;

const {Express} = require(paths.code + '/express');

class ExtensibleExpress extends Express {

  static templatesFolder = [];

  _createApp({isProxy = ![]} = {}) {
    const {extensibleFoundry} = global;
    const app = super._createApp({'isProxy': isProxy});
    extensibleFoundry.hooks.call('post.express.createApp', app);
    return app;
  }

  _defineRoutes(router) {
    const {extensibleFoundry} = global;
    extensibleFoundry.hooks.call('pre.express.defineRoutes', router);
    super._defineRoutes(router);
  }
}

module.exports = {'Express': ExtensibleExpress};
