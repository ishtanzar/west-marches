import Express from 'foundry:dist/server/express.mjs';

export default class ExtensibleExpress extends Express {

  _defineRoutes(router) {
    const {extensibleFoundry} = global;
    extensibleFoundry.hooks.call('pre.express.defineRoutes', router);
    super._defineRoutes(router);
  }

}