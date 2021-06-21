'use strict';

const prom = require('prom-client');

(function init() {
  setTimeout(function() {
    /** @type e.Router */
    const router = global.express && global.express.app && global.express.app._router;
    if(router) {
      const prefixPart = global.config.options.routePrefix ? `/${global.config.options.routePrefix}/` : "/";
      router.get(`${prefixPart}metrics`, FoundryMetrics.get);

      prom.collectDefaultMetrics();
    } else {
      init();
    }
  }, 1000);
})();

class FoundryMetrics {
  static async get(req, res) {
    try {
      res.set('Content-Type', prom.register.contentType)
      res.send(await prom.register.metrics());
    } catch (ex) {
      res.status(500).end(ex);
    }
  }
}

