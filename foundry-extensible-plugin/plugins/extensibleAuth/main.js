
const path = require('path');
const fetch = require('node-fetch');
const express = require('express');

let _extensiblePlugin;

let _options = {
  providers: {
    access_key: {
      enabled: true,
    },
    discord: {
      enabled: true,
    }
  }
};

const _DEFAULTS = {
  oauth: {
    discord: {
      redirect_uri: 'http://localhost:30000/oauth/authenticate/discord'
    }
  }
}

const scripts = [
  'init'
]

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

async function route_settings(req, resp) {
  let settings = [{
    module: 'foundry-extensible-auth-module',
    key: 'access_key.enabled',
    name: 'ExtensibleAuth.AccessKkey.Enabled.Name',
    scope: 'world',
    config: true,
    type: 'Boolean',
    default: false
  }];
  await _extensiblePlugin.hooks.callAsync('extensibleAuth.route_settings.settings', settings);

  resp.send({
    settings: settings
  });
}

async function route_join(req, resp) {
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
    },
    'oauth': {}
  };

  await _extensiblePlugin.hooks.callAsync('extensibleAuth.route_join.auths', auths);

  return resp.render('join', {
    users: users,
    world: game.world.data,
    bodyClass: "vtt players " + (bgClass ? "background" : ''),
    bodyStyle: 'background-image:\x20url(\x27' + (bgClass || "ui/denim075.png") + '\x27)',
    messages: auth.sessions.getMessages(req),
    auths: auths
  });
}

async function route_oauth_authenticate(req, resp) {
  _extensiblePlugin.hooks.call('extensibleAuth.route_oauth_authenticate', req, resp);
}

async function route_validate(req, resp) {
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

class ExtensibleAuthFoundryPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    _extensiblePlugin = base;

    _extensiblePlugin.hooks.call('pre.extensibleAuth.constructor', this);

    _extensiblePlugin.hooks.once('post.express.createApp', app => {
      app.set('views', [path.join(__dirname, 'templates', 'views')].concat(app.get('views')));
    });

    _extensiblePlugin.hooks.once('pre.express.defineRoutes', router => {
      router.use('/modules/extensibleAuth', express.static(path.join(__dirname, 'foundry-extensible-auth-module'), {'redirect': false}));
      router.get('/extensibleAuth/settings', route_settings);
      router.get('/oauth/authenticate/:service', route_oauth_authenticate);
      router.get('/join', route_join.bind(this));
      router.post('/oauth/discord/authenticate', route_validate);
    });

    _extensiblePlugin.hooks.on('post.world.constructor', async world => {
      world.modules.push({
        "data": {
          "name": "foundry-extensible-auth-module",
          "title": "ExtensibleAuth",
          "description": "A module that pairs with the ExtensibleAuth plugin",
          "author": "ishtanzar",
          "version": "0.0.1",
          "minimumCoreVersion": "0.7.9",
          "esmodules": [],
          'packs': [],
          'styles': [],
          'scripts': scripts.map(item => { return `./scripts/${item}` })
        },
        "id": "foundry-extensible-auth-module",
        "path": path.join(__dirname, 'foundry-extensible-auth-module'),
        "esmodules": [],
        'languages': [],
        'packs': [],
        'styles': [],
        'scripts': scripts.map(item => { return `modules/extensibleAuth/scripts/${item}.js` })
      });

    });

    _extensiblePlugin.hooks.once('post.world.setup', async world => {
      const {paths} = global;
      const {Setting} = require(path.join(paths.code, 'database', 'documents', 'settings'));
      const moduleConfiguration = await Setting.get('core.moduleConfiguration');

      if(!('foundry-extensible-auth-module' in moduleConfiguration)) {
        moduleConfiguration['foundry-extensible-auth-module'] = true;
        await Setting.set('core.moduleConfiguration', moduleConfiguration);
      }
    });
    _extensiblePlugin.hooks.call('post.extensibleAuth.constructor', this);
  }
}

module.exports = ExtensibleAuthFoundryPlugin;
