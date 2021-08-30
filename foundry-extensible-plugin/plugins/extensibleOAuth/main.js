
const path = require('path');
const discordAuth = require('./discord');

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
      router.get('/join', discordAuth.join);
      router.post('/discord/validate', discordAuth.validate);
      router.get('/login/discord', discordAuth.doLogin);
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
