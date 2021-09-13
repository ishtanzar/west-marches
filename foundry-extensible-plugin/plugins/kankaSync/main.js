const fetch = require('node-fetch');
const path = require('path');
const express = require('express');

const scripts = [
  'init'
]

const _DEFAULTS = {
  oauth: {
    redirect_uri: 'http://localhost:30000/oauth/authenticate/kanka'
  }
}

class InvalidAccessTokenError extends Error {}

async function _validateAccessToken(access_token) {
  const userResult = await fetch('https://kanka.io/api/1.0/profile', {
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
  const {db, paths, logger} = global;
  const service = req.params.service;
  const code = req.query.code;

  if(service === 'kanka') {
    const redirect_uri = await db.Setting.get('kanka-sync-module.oauth.redirectUri');
    const auth = require(paths.code + '/auth');

    const oauthResult = await fetch('https://kanka.io/oauth/token', {
      method: 'POST',
      body: new URLSearchParams({
        client_id: await db.Setting.get('kanka-sync-module.oauth.clientId'),
        client_secret: await db.Setting.get('kanka-sync-module.oauth.clientSecret'),
        code,
        grant_type: 'authorization_code',
        redirect_uri: redirect_uri ? redirect_uri : _DEFAULTS.oauth.redirect_uri,
        // scope: 'identify',
      }),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });

    if(oauthResult.ok) {
      const oauthData = await oauthResult.json();
      const kanka = await _validateAccessToken(oauthData.access_token);
      const session = auth.sessions.get(req, resp);
      const userId = Object.values(session.worlds || {})[0];

      if(userId) {
        const user = await db.User.findOne( {'_id': userId} );
        user.update({
          auth: {
            kanka: {
              access_token: oauthData.access_token,
              refresh_token: oauthData.refresh_token,
              expires_in: oauthData.expires_in,
              logging_date: Date.now()
            }
          },
          kanka: kanka.data
        }).save();

        logger.info(`User ${user.name} logged on kanka with username ${kanka.data.name}`);
        resp.render('kanka-oauth', {
          'access_token': oauthData.access_token
        });
      }
    }
  }
}

class KankaSyncPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {

    base.hooks.on('extensibleAuth.route_oauth_authenticate', route_oauth_authenticate);
    base.hooks.once('pre.express.defineRoutes', router => {
      router.use('/modules/kankaSync', express.static(path.join(__dirname, 'kanka-sync-module'), {'redirect': false}));
    });

    base.hooks.once('post.express.createApp', app => {
      app.set('views', [path.join(__dirname, 'templates', 'views')].concat(app.get('views')));
    });

    base.hooks.on('post.world.constructor', async world => {
      world.modules.push({
        "data": {
          "name": "kanka-sync-module",
          "title": "KankaSync",
          "description": "A module to sync data to Kanka",
          "author": "ishtanzar",
          "version": "0.0.1",
          "minimumCoreVersion": "0.7.9",
          "esmodules": [],
          'packs': [],
          'styles': [],
          'scripts': scripts.map(item => { return `./scripts/${item}` })
        },
        "id": "kanka-sync-module",
        "path": path.join(__dirname, 'kanka-sync-module'),
        "esmodules": [],
        'languages': [],
        'packs': [],
        'styles': [],
        'scripts': scripts.map(item => { return `modules/kankaSync/scripts/${item}.js` })
      });
    });

    base.hooks.once('post.world.setup', async world => {
      const {paths} = global;
      const {Setting} = require(path.join(paths.code, 'database', 'documents', 'settings'));
      const moduleConfiguration = await Setting.get('core.moduleConfiguration');

      if(!('kanka-sync-module' in moduleConfiguration)) {
        moduleConfiguration['kanka-sync-module'] = true;
        await Setting.set('core.moduleConfiguration', moduleConfiguration);
      }
    });

    base.hooks.on('post.user.schema', schema => {
      schema['kanka'] = {
        'type': Object,
        'required': !![],
        'default': {},
        'validate': () => true,
        'validationError': 'Invalid auth object structure'
      }
    });
  }
}

module.exports = KankaSyncPlugin;
