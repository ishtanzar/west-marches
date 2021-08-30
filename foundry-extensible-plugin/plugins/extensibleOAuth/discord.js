'use strict';

const fetch = require('node-fetch');

async function fetch_setting(key, default_value = null) {
  const {db} = global;
  const json_value = await db.Setting.findOne({'key': key});

  return json_value ? JSON.parse(json_value.value) : default_value;
}

class InvalidAccessTokenError extends Error {
}

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

const SETTINGS = {
  CLIENT_ID: 'wm-foundry-module.oauthClientId',
  CLIENT_SECRET: 'wm-foundry-module.oauthClientSecret',
  REDIRECT_URI: 'wm-foundry-module.oauthRedirectUri',
}

module.exports = {
  async join(req, resp) {
    const {db, game, paths} = global;
    const Views = require(paths.code + '/views');
    const auth = require(paths.code + '/auth');

    if (!game.world) return Views["noWorld"](req, resp);
    if (!game.ready) return setTimeout(() => Views['join'](req, resp), 1000);

    auth.sessions.logoutWorld(req, resp);

    const users = await db.User.getUsers();
    users.forEach(user => user['active'] = user.isActive);
    const bgClass = game.world ? game.world.background : null;

    const auths = {
      'access_key': {
        'enabled': true,
        'users': users
      }
    };

    auths['oauth_discord'] = {
      enabled: true,
      client_id: await fetch_setting(SETTINGS.CLIENT_ID),
      redirect_uri: await fetch_setting(SETTINGS.REDIRECT_URI),
      scopes: 'identify',
    }

    return resp.render('join', {
      users: users,
      world: game.world.data,
      bodyClass: "vtt players " + (bgClass ? "background" : ''),
      bodyStyle: 'background-image:\x20url(\x27' + (bgClass || "ui/denim075.png") + '\x27)',
      messages: auth.sessions.getMessages(req),
      auths: auths
    });
  },

  async doLogin(req, resp) {
    const {db, game, paths, logger} = global;
    const code = req.query.code;
    const auth = require(paths.code + '/auth');

    const oauthResult = await fetch('https://discord.com/api/oauth2/token', {
      method: 'POST',
      body: new URLSearchParams({
        client_id: await fetch_setting(SETTINGS.CLIENT_ID),
        client_secret: await fetch_setting(SETTINGS.CLIENT_SECRET),
        code,
        grant_type: 'authorization_code',
        redirect_uri: await fetch_setting(SETTINGS.REDIRECT_URI),
        scope: 'identify',
      }),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });

    const oauthData = await oauthResult.json();
    const discord = await _validateAccessToken(oauthData.access_token);

    const user = await db.User.findOne({ $or: [{'name': discord.username}, {'discord.id': discord.id}] });
    if (user === null) {
      resp.status(403);
      // return {'request': 'join', 'status': "failed", 'error': "The requested User ID " + userid + " does not exist."};
    }
    if (user.role === 0) {
      resp.status(403);
      // return {
      //   'request': "join",
      //   'status': "failed",
      //   'error': "User " + user.name + " does not have permission to access this World."
      // };
    }

    user.update({
      'discord': discord,
      'auth': {
        'discord': {
          'access_token': oauthData.access_token,
          'refresh_token': oauthData.refresh_token,
          'expires_in': oauthData.expires_in,
          'logging_date': Date.now()
        }
      }
    }).save();

    auth.sessions.logoutWorld(req, resp);
    const session = auth.sessions.getOrCreate(req, resp);
    session['worlds'][game.world.id] = user['_id'];

    logger.info('User\x20authentication\x20successful\x20for\x20user\x20' + user.name);
    resp.render('oauth-discord', {
      'access_token': oauthData.access_token,
      'refresh_token': oauthData.refresh_token,
    });
  },

  async validate(req, resp) {
    try {
      const access_token = req.body.access_token;
      if(access_token) {
          await _validateAccessToken(access_token);
      }
      resp.sendStatus(204);
    } catch (e) {
      if(e instanceof InvalidAccessTokenError) return resp.sendStatus(401);
      resp.sendStatus(500);
    }
  }
}
