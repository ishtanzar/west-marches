'use strict';

const fetch = require('node-fetch');

class DiscordOAuth {

  async fetch_setting(key) {
    const {db} = global;
    return JSON.parse((await db['Setting'].findOne({'key': key})).value)
  }

  async client_id() {
    return await this.fetch_setting('wm-cave-du-roliste.oauthClientId');
  }

  async client_secret() {
    return await this.fetch_setting('wm-cave-du-roliste.oauthClientSecret');
  }

  async redirect_uri() {
    return await this.fetch_setting('wm-cave-du-roliste.oauthRedirectUri');
  }

  replaceJoinRoute(expressRouter, prefix='/') {
    const foundryStack = expressRouter.stack.find(layer => layer.name == 'router').handle.stack;

    foundryStack.splice(foundryStack.findIndex(
      layer => layer.route && layer.route.path == '/join' && layer.route.methods['get'] == true
    ), 1);

    expressRouter.get(`${prefix}join`, this.login.bind(this));
    // const stack = router.stack.find(layer => layer.name == 'router').handle.stack
  }

  async login(req, resp) {
    const {db, game, paths} = global;
    const Views = require(paths.code + '/views');
    const auth = require(paths.code + '/auth');

    if (!game.world) return Views["noWorld"](req, resp);
    if (!game.ready) return setTimeout(() => Views['join'](req, resp), 1000);

    auth.sessions.logoutWorld(req, resp);

    const users = await db['User'].getUsers();
    users.forEach(user => user["active"] = user.isActive);
    const bgClass = game.world ? game.world.background : null;

    const auths = {
      'access_key': {
        'enabled': true,
        'users': users
      }
    };

    auths['oauth'] = {
      'enabled': true,
      'client_id': await this.client_id(),
      'redirect_uri': await this.redirect_uri(),
      'scopes': 'identify',
    }

    return resp.render('join', {
      'users': users,
      'world': game.world.data,
      'bodyClass': "vtt players " + (bgClass ? "background" : ''),
      'bodyStyle': 'background-image:\x20url(\x27' + (bgClass || "ui/denim075.png") + '\x27)',
      'messages': auth.sessions.getMessages(req),
      'auths': auths
    });
  }

  async doLogin(req, resp) {
    const {db, game, paths} = global;
    const code = req.query.code
    const auth = require(paths.code + '/auth');

    const oauthResult = await fetch('https://discord.com/api/oauth2/token', {
      method: 'POST',
      body: new URLSearchParams({
        client_id: await this.client_id(),
        client_secret: await this.client_secret(),
        code,
        grant_type: 'authorization_code',
        redirect_uri: await this.redirect_uri(),
        scope: 'identify',
      }),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });

    const oauthData = await oauthResult.json();
    const userResult = await fetch('https://discord.com/api/users/@me', {
      headers: {
        authorization: `${oauthData.token_type} ${oauthData.access_token}`,
      },
    });

    const userData = await userResult.json();
    const user = await db["User"].findOne({'name': userData['username']});
    if (user === null) {
      resp.status = 403
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

    auth.sessions.logoutWorld(req, resp);
    const session = auth.sessions.getOrCreate(req, resp);
    session["worlds"][game.world.id] = user["_id"];

    global.logger.info('User\x20authentication\x20successful\x20for\x20user\x20' + user.name);
    resp.redirect(req['baseUrl'] + '/game');
    /**
     * {
  id: '323793120787693569',
  username: 'ishtanzar',
  avatar: 'a15742db3af87d71a0bb06862434cc64',
  discriminator: '9779',
  public_flags: 0,
  flags: 0,
  banner: null,
  banner_color: null,
  accent_color: null,
  locale: 'fr',
  mfa_enabled: true,
  email: 'pgmillon@gmail.com',
  verified: true
}

     */
  }

}

module.exports = DiscordOAuth;
