import Express from 'foundry:dist/server/express.mjs';

export default class ExtensibleExpress extends Express {

  _defineRoutes(router) {
    extensibleFoundry.hooks.call('pre.express.defineRoutes', router);
    super._defineRoutes(router);
    extensibleFoundry.hooks.call('post.express.defineRoutes', router);
  }

  _createApp({compressStatic: compressStatic = false, isProxy: isProxy = false} = {}) {
    const app = super._createApp({compressStatic: compressStatic, isProxy: isProxy});
    extensibleFoundry.hooks.call('post.express.createApp', app);
    return app;
  }

  _middleware(router) {
    extensibleFoundry.hooks.call('pre.express.middleware', router);
    super._middleware(router);
    extensibleFoundry.hooks.call('post.express.middleware', router);
  }

  static _userSessionMiddleware(req, resp, next) {
    if(req.path.startsWith('/api') || req.path.startsWith('/metrics')) {
      next()
    } else {
      Express._userSessionMiddleware(req, resp, next);
    }
  }

  _staticFiles(express) {
    extensibleFoundry.hooks.call('pre.express.staticFiles', express);
    super._staticFiles(express);
    extensibleFoundry.hooks.call('post.express.staticFiles', express);
  }

  async listen(socket) {
    extensibleFoundry.hooks.call('pre.express.listen', this, socket);
    await super.listen(socket);
    extensibleFoundry.hooks.call('post.express.listen', this, socket);
  }

}