import path from "path";
import url from "url";
import fetch from "node-fetch";
import sessions from "foundry:dist/sessions.mjs";
import Express from "foundry:dist/server/express.mjs";

class InvalidAccessTokenError extends Error {}

export default class ExtensibleDiscordOAuthPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    const pluginRoot = path.dirname(url.fileURLToPath(import.meta.url));

    base.hooks.on('post.user.defineSchema', this.updateUserSchema);
    base.hooks.on('pre.api.user.create', this.create_user);
    base.hooks.on('extensibleAuth.route_oauth_authenticate', this.route_oauth_authenticate.bind(this));
    base.hooks.on('extensibleAuth.register_method', callback => callback({
      id: 'discord',
      module_name: 'extensible-auth-discord-client',
      title: 'ExtensibleAuth Discord Plugin',
      scripts: ['./scripts/init.js'],
      languages: [
        { lang: "en", name: "English", path: "languages/en.json" }
      ],
      root: path.join(pluginRoot)
    }));

    base.addTemplateDirectory(pluginRoot);
    base.addViewsDirectory(path.join(pluginRoot, 'templates', 'views'));
  }

  updateUserSchema(schema) {
    Object.assign(schema, {
      discord: {
        type: Object,
        required: false,
        default: {}
      }
    });
  }

  create_user(req, resp, user_data) {
    user_data['discord'] = req.body.discord || {};
  }

  async route_oauth_authenticate(req, resp) {
    const {db, game, extensibleLogger, logger} = global;

    const code = req.query.code;
    const service = req.params.service;

    if(service === 'discord') {
      const redirect_uri = await db.Setting.getValue('extensible-auth.method.discord.redirectUri');
      const oauthResult = await fetch('https://discord.com/api/oauth2/token', {
        method: 'POST',
        body: new URLSearchParams({
          client_id: await db.Setting.getValue('extensible-auth.method.discord.clientId'),
          client_secret: await db.Setting.getValue('extensible-auth.method.discord.clientSecret'),
          code,
          grant_type: 'authorization_code',
          redirect_uri: redirect_uri,
          scope: 'identify',
        }),
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        }
      });

      if(oauthResult.ok) {
        extensibleLogger.debug('Discord OAuth authorized');
        const oauthData = await oauthResult.json();
        const discord = await this._validateAccessToken(oauthData.access_token);

        const [user] = await db.User.find({ $or: [{'name': discord.username}, {'discord.id': discord.id}] });
        if (user === null) {
          extensibleLogger.warn(`No such user: ${discord.username}/${discord.id}`)
          return resp.status(403).send('Failed to authenticate, please contact a site admin.');
        }
        if (user.role === 0) {
          extensibleLogger.warn(`User: ${discord.username}/${discord.id} does not have permission to access this World.`)
          return resp.status(403).send('Failed to authenticate, please contact a site admin.');
        }

        //TODO: update username with discriminator

        // user.update({
        //   discord: discord,
        //   auth: {
        //     discord: {
        //       access_token: oauthData.access_token,
        //       refresh_token: oauthData.refresh_token,
        //       expires_in: oauthData.expires_in,
        //       logging_date: Date.now()
        //     }
        //   }
        // }).save();

        sessions.logoutWorld(req, resp);
        const session = sessions.getOrCreate(req, resp);
        session.worlds[game.world.id] = user.id;

        logger.info(`User authentication successful for user ${user.name}`, {
          session: session.id,
          ip: req.ip
        });

        const scripts = [], styles = [], srcToContent = (src, type, priority) => {
          const content = {src: '/' + src, type: type, priority: priority, isModule: "module" === type}
          if(type === "style") {
            styles.push(content)
          } else {
            scripts.push(content)
          }
        }

        Express.CORE_VIEW_SCRIPTS.forEach(script => srcToContent(script, 'script', 0));
        Express.CORE_VIEW_STYLES.forEach(script => srcToContent(script, 'style', 1));
        game.world.styles.forEach(script => srcToContent(script, 'style', 4));
        game.world.scripts.forEach(script => srcToContent(script, 'script', 9));

        resp.render('discord_authenticate', {
          bodyClass: "vtt players",
          access_token: oauthData.access_token,
          refresh_token: oauthData.refresh_token,
          scripts: scripts,
          styles: styles
        });
      } else {
        logger.warn(`User authentication failed;` + await oauthResult.text(), {
          ip: req.ip
        })
        resp.status(oauthResult.status).send('Failed to authenticate, please contact a site admin.');
      }
    }
  }

  async _validateAccessToken(access_token) {
    const userResult = await fetch('https://discord.com/api/users/@me', {
      headers: {
        authorization: `Bearer ${access_token}`,
      },
    });

    if(userResult.status >= 400) {
      throw new InvalidAccessTokenError();
    }

    extensibleLogger.debug('Discord OAuth access token validated');
    return userResult.json();
  }

}