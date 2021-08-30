
const path = require('path');
const {DiscordOAuth} = require('./discord');

const discordAuth = new DiscordOAuth();

class ExtensibleOAuthFoundryPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    base.hooks.once('post.express.createApp', app => {
      app.set('views', [path.join(__dirname, 'templates', 'views')].concat(app.get('views')));
    });

    base.hooks.once('pre.express.defineRoutes', router => {
      router.get('/join', discordAuth.join.bind(discordAuth));
      router.get('/login/discord', discordAuth.doLogin.bind(discordAuth));
    });

    base.hooks.once('user.schema', schema => {
      schema['discord'] = {
        'type': Object,
        'required': !![],
        'default': {},
        'validate': () => true,
        'validationError': 'Invalid discord object structure'
      }

      schema['auth'] = {
        'type': Object,
        'required': !![],
        'default': {},
        'validate': () => true,
        'validationError': 'Invalid auth object structure'
      }

    });
  }
}

module.exports = ExtensibleOAuthFoundryPlugin;
