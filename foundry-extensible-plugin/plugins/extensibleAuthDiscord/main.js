const fetch = require('node-fetch');
const path = require('path');

const _DEFAULTS = {
  oauth: {
    discord: {
      redirect_uri: 'http://localhost:30000/oauth/authenticate/discord'
    }
  }
}

class InvalidAccessTokenError extends Error {}

async function _validateAccessToken(access_token) {
  const userResult = await fetch('https://discord.com/api/users/@me', {
    headers: {
      authorization: `Bearer ${access_token}`,
    },
  });

  if(userResult.status >= 400) {
    throw new InvalidAccessTokenError();
  }

  return userResult.json();
}

async function route_oauth_authenticate(req, resp) {
  const {db, game, paths, logger} = global;
  const auth = require(paths.code + '/auth');

  const code = req.query.code;
  const service = req.params.service;

  if(service === 'discord') {
    const redirect_uri = await db.Setting.get('foundry-extensible-auth-module.oauth.discord.redirectUri');
    const oauthResult = await fetch('https://discord.com/api/oauth2/token', {
      method: 'POST',
      body: new URLSearchParams({
        client_id: await db.Setting.get('foundry-extensible-auth-module.oauth.discord.clientId'),
        client_secret: await db.Setting.get('foundry-extensible-auth-module.oauth.discord.clientSecret'),
        code,
        grant_type: 'authorization_code',
        redirect_uri: redirect_uri ? redirect_uri : _DEFAULTS.oauth.discord.redirect_uri,
        scope: 'identify',
      }),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });

    if(oauthResult.ok) {
      const oauthData = await oauthResult.json();
      const discord = await _validateAccessToken(oauthData.access_token);

      const user = await db.User.findOne({ $or: [{'name': discord.username}, {'discord.id': discord.id}] });
      if (user === null) {
        logger.warn(`No such user: ${discord.username}/${discord.id}`)
        return resp.status(403).send('Failed to authenticate, please contact a site admin.');
      }
      if (user.role === 0) {
        logger.warn(`User: ${discord.username}/${discord.id} does not have permission to access this World.`)
        return resp.status(403).send('Failed to authenticate, please contact a site admin.');
      }

      user.update({
        discord: discord,
        auth: {
          discord: {
            access_token: oauthData.access_token,
            refresh_token: oauthData.refresh_token,
            expires_in: oauthData.expires_in,
            logging_date: Date.now()
          }
        }
      }).save();

      auth.sessions.logoutWorld(req, resp);
      const session = auth.sessions.getOrCreate(req, resp);
      session['worlds'][game.world.id] = user['_id'];

      logger.info('User\x20authentication\x20successful\x20for\x20user\x20' + user.name);
      resp.render('oauth-discord', {
        access_token: oauthData.access_token,
        refresh_token: oauthData.refresh_token,
      });
    } else {
      logger.warn('Failed to authenticate user: ' + await oauthResult.text())
      resp.status(oauthResult.status).send('Failed to authenticate, please contact a site admin.');
    }
  }
}

class ExtensibleDiscordOAuthPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    base.hooks.on('extensibleAuth.route_oauth_authenticate', route_oauth_authenticate);
    base.hooks.on('extensibleAuth.route_join.auths', this.configure);
    base.hooks.on('extensibleAuth.route_settings.settings', this.get_settings);

    base.hooks.once('post.express.createApp', app => {
      app.set('views', [path.join(__dirname, 'templates', 'views')].concat(app.get('views')));
    });

    base.hooks.on('pre.express-handlebars.config', config => {
      config.partialsDir = (config.partialsDir || []).concat([path.join(__dirname, 'templates', 'views', 'partials')])
    });

    base.hooks.on('post.user.schema', schema => {
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

    base.hooks.on('pre.api.user.create', (req, resp, user_data) => {
      user_data['discord'] = req.body.discord || {};
    });
  }

  async configure(auths) {
    const {db} = global;

    if(await db.Setting.get('foundry-extensible-auth-module.oauth.discord.enabled')) {
      const client_id = await db.Setting.get('foundry-extensible-auth-module.oauth.discord.clientId');
      let redirect_uri = await db.Setting.get('foundry-extensible-auth-module.oauth.discord.redirectUri');

      auths['oauth_discord'] = {
        enabled: true,
        client_id: client_id,
        redirect_uri: redirect_uri ? redirect_uri : _DEFAULTS.oauth.discord.redirect_uri,
        scopes: 'identify',
      }
    }
  }

  async get_settings(settings) {
    [
      {
        module: 'foundry-extensible-auth-module',
        key: 'oauth.discord.enabled',
        name: 'ExtensibleAuth.OAuth.Discord.Enabled.Name',
        scope: 'world',
        config: true,
        type: 'Boolean',
        default: false
      },
      {
        module: 'foundry-extensible-auth-module',
        key: 'oauth.discord.clientId',
        name: 'ExtensibleAuth.OAuth.Discord.ClientId.Name',
        scope: 'world',
        config: true,
        type: 'String',
        default: ''
      },
      {
        module: 'foundry-extensible-auth-module',
        key: 'oauth.discord.clientSecret',
        name: 'ExtensibleAuth.OAuth.Discord.ClientSecret.Name',
        scope: 'world',
        config: true,
        type: 'String',
        default: ''
      },
      {
        module: 'foundry-extensible-auth-module',
        key: 'oauth.discord.redirectUri',
        name: 'ExtensibleAuth.OAuth.Discord.RedirectUri.Name',
        scope: 'world',
        config: true,
        type: 'String',
        default: _DEFAULTS.oauth.discord.redirect_uri
      },
    ].map(setting => {settings.push(setting)});
  }

}

module.exports = ExtensibleDiscordOAuthPlugin;