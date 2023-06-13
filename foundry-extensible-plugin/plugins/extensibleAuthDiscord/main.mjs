import path from "path";
import url from "url";
import fetch from "node-fetch";
import sessions from "foundry:dist/sessions.mjs";
import Express from "foundry:dist/server/express.mjs";
import { randomBytes } from "crypto";

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
    base.hooks.on('post.extensibleAuth.getLoginData', this.getLoginData.bind(this));
    base.hooks.on('extensiblePlugins.migrate', this.migrate.bind(this));
    base.hooks.on('extensibleAuth.method.register', register => register({
      id: 'discord',
      name: 'extensibleAuthDiscord',
      title: 'ExtensibleAuth Discord Plugin',
      esmodules: ['modules/main.mjs'],
      languages: [
        { lang: "en", name: "English", path: "languages/en.json" }
      ],
      path: pluginRoot,
    }));
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

  async getLoginData(data) {
    const oauth_endpoint = await db.Setting.getValue('extensibleAuth.method.discord.oauthEndpoint');

    data.discord = {
      client_id: await db.Setting.getValue('extensibleAuth.method.discord.clientId'),
      redirect_uri: await db.Setting.getValue('extensibleAuth.method.discord.redirectUri'),
      oauth_endpoint: oauth_endpoint.length > 0 ? oauth_endpoint : 'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}',
      scopes: 'identify'
    }
  }

  async migrate() {
    const v0Settings = {}, v1Settings = {}, v2Settings = {};
    const settingKeys = ['clientId', 'clientSecret', 'redirectUri', 'enabled'];

    for(let setting of await db.Setting.find({key: /extensible-?[Aa]uth.*discord/})) {
      for(let key of settingKeys) {
        if(setting.key.match(new RegExp(`^foundry-extensible.*${key}$`))) {
          v0Settings[key] = setting.value;
          await setting.delete();
          continue;
        }
        if(setting.key.match(new RegExp(`^extensible-auth.*${key}$`))) {
          v1Settings[key] = setting.value;
          await setting.delete();
          continue;
        }
        if(setting.key.match(new RegExp(`^extensibleAuth.*${key}$`))) {
          v2Settings[key] = setting.value;
        }
      }
    }

    if(Object.keys(v0Settings).length || Object.keys(v1Settings).length) {
      for(let key of settingKeys) {
        const existingValue = v2Settings.hasOwnProperty(key) ? v2Settings[key] : undefined;
        v2Settings[key] = v2Settings.hasOwnProperty(key) ? v2Settings[key] : v1Settings.hasOwnProperty(key) ? v1Settings[key] : v0Settings.hasOwnProperty(key) ? v0Settings[key] : undefined;

        if(existingValue !== v2Settings[key]) {
          await db.Setting.set(`extensibleAuth.method.discord.${key}`, JSON.stringify(v2Settings[key]));
        }
      }
    }
  }

  async route_oauth_authenticate(req, resp) {
    const {db, game, extensibleLogger, logger} = global;

    const code = req.query.code;
    const service = req.params.service;

    if(service === 'discord') {
      const redirect_uri = await db.Setting.getValue('extensibleAuth.method.discord.redirectUri');
      const oauthResult = await fetch('https://discord.com/api/oauth2/token', {
        method: 'POST',
        body: new URLSearchParams({
          client_id: await db.Setting.getValue('extensibleAuth.method.discord.clientId'),
          client_secret: await db.Setting.getValue('extensibleAuth.method.discord.clientSecret'),
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

        await user.update({
          password: randomBytes(16).toString('hex'),
          discord: discord,
          auth: {
            discord: {
              logging_date: Date.now()
            }
          }
        });

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