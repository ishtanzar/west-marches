import Express from 'foundry:dist/server/express.mjs';

export default class ExtensibleExpress extends Express {

  _defineRoutes(router) {
    const {extensibleFoundry} = global;
    extensibleFoundry.hooks.call('pre.express.defineRoutes', router);
    super._defineRoutes(router);
  }

  static get CORE_VIEW_MODULES() {
    const modules = Express.CORE_VIEW_MODULES;
    extensibleFoundry.hooks.call('post.express.CORE_VIEW_MODULES', modules);
    return modules;
  }

  static get CORE_VIEW_SCRIPTS() {
    const scripts = Express.CORE_VIEW_SCRIPTS;
    extensibleFoundry.hooks.call('post.express.CORE_VIEW_SCRIPTS', scripts);
    return scripts;
  }

  _staticFiles(express) {
    super._staticFiles(express);
    extensibleFoundry.hooks.call('post.express.staticFiles', express);
  }

}