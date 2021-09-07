'use strict';

const cookie = require('cookie')
const jwt = require("jsonwebtoken");

async function route_home(req, resp) {
  const {db, game, paths, logger} = global;
  const auth = require(paths.code + '/auth');

  if (game.world) {
    if(req.headers.cookie) {
      const cookies = cookie.parse(req.headers.cookie);
      if(cookies.access_token) {
        try {
          const decoded = jwt.verify(cookies.access_token, 'mySecret');

          const user = await db.User.findOne({'_id': decoded.user_id});
          if (user && user.role > 0) {
            auth.sessions.logoutWorld(req, resp);
            const session = auth.sessions.getOrCreate(req, resp);
            session['worlds'][game.world.id] = user['_id'];

            logger.info('User\x20authentication\x20successful\x20for\x20user\x20' + user.name);

            return resp.redirect(req.baseUrl + '/game');
          }
        } catch (e) {
          logger.warn(`Could not verify JWT: ${e.message}`)
        }
      }
    }
    return resp.redirect(req.baseUrl + '/join');
  }
  return resp.redirect(req.baseUrl + '/setup');
}

class ExtensibleJwtAuthPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {

    base.hooks.on('post.auth.authenticateUser', async (req, resp, result) => {
      const json = await result;
      if(json.status === 'success') {
        const token = jwt.sign({
          user_id: req.body.userid,
          auth_service: 'access_key'
        }, 'mySecret', {
          expiresIn: '2h',
          audience: 'westmarchesdelacave.ishtanzar.net',
          issuer: 'westmarchesdelacave.ishtanzar.net'
        })

        resp.cookie('access_token', token, {
          httpOnly: true
        })
      }
    });

    base.hooks.on('pre.views.home', async params => {
      params.replace = true;
      params.result = route_home(params.req, params.resp);
    });
  }
}

module.exports = ExtensibleJwtAuthPlugin;
