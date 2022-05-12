import Express from 'foundry:dist/server/express.mjs';

export default class ExtensibleExpress extends Express {

  _defineRoutes(router) {
    extensibleFoundry.hooks.call('pre.express.defineRoutes', router);
    super._defineRoutes(router);
  }

  _createApp({isProxy: isProxy = false} = {}) {
    const app = super._createApp({'isProxy': isProxy});
    extensibleFoundry.hooks.call('post.express.createApp', app);
    return app;
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
    extensibleFoundry.hooks.call('pre.express.staticFiles', express);
    super._staticFiles(express);
    extensibleFoundry.hooks.call('post.express.staticFiles', express);
  }

}