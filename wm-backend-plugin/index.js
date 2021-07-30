'use strict';

const FoundryMetrics = require('./metrics');
const Roster = require('./roster');
const DiscordOAuth = require('./auth');
const path = require('path');

const foundryMetrics = new FoundryMetrics();
const foundryRoster = new Roster();
const discordAuth = new DiscordOAuth();

console.log('WestMarches | init');

(function init() {
  setTimeout(function() {
    /** @type e.Router */
    const router = global.express && global.express.app && global.express.app._router;
    if(router) {
      console.log('WestMarches | setup');
      const app = global.express.app;
      const prefixPart = global.config.options.routePrefix ? `/${global.config.options.routePrefix}/` : "/";

      app.set('views', [path.join(__dirname, 'templates', 'views'), app.get('views')]);

      router.get(`${prefixPart}metrics`, foundryMetrics.get);
      router.get(`${prefixPart}actors`, foundryRoster.get);
      router.get(`${prefixPart}login/discord`, discordAuth.doLogin.bind(discordAuth));

      foundryMetrics.setup().update().schedule();

      discordAuth.replaceJoinRoute(router, prefixPart);
    } else {
      init();
    }
  }, 1000);
})();
