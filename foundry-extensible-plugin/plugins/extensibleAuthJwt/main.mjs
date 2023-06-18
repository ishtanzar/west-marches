import sessions from "foundry:dist/sessions.mjs";
import Express from "foundry:dist/server/express.mjs";
import jwt from "jsonwebtoken";
import cookie from "cookie";
import path from "path";
import url from "url";

export default class ExtensibleJwtAuthPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    const pluginRoot = path.dirname(url.fileURLToPath(import.meta.url));

    base.hooks.on('pre.express.userSessionMiddleware', this.jwt_middleware.bind(this));
    base.hooks.on('extensibleAuth.route_oauth_authenticate', this.route_oauth_authenticate.bind(this));
    base.hooks.on('extensibleAuth.method.register', register => register({
      id: 'jwt',
      name: 'extensibleAuthJwt',
      title: 'ExtensibleAuth JWT Plugin',
      esmodules: ['modules/main.mjs'],
      languages: [
        { lang: "en", name: "English", path: "languages/en.json" }
      ],
      path: pluginRoot,
    }));
  }

  async jwt_middleware(req, resp, next) {
    const {db, game, logger} = global;
    if(game.world) {
      const is_enabled = await db.Setting.getValue('extensibleAuth.method.jwt.enabled');

      let api_endpoint = await db.Setting.getValue('extensibleAuth.method.jwt.api_endpoint');
      const api_headers = {
        Accept: 'application/json',
        Authorization: 'ApiKey-v1 ' + await db.Setting.getValue('extensibleAuth.method.jwt.api_key'),
        'Content-type': 'application/json'
      };

      if(is_enabled && req.headers.cookie) {
        const cookies = cookie.parse(req.headers.cookie);

        if(cookies.access_token) {
          try {
            logger.debug('Verifying JWT');
            const decoded = jwt.verify(
                cookies.access_token,
                await db.Setting.getValue('extensibleAuth.method.jwt.shared_key')
            );

            api_endpoint ||= "http://api:3000";
            const api_url = `${api_endpoint}/users/${decoded.user_id}`;
            logger.debug(`Fetching user data from API ${decoded.user_id}`);
            const api_get = await fetch(api_url, {headers: api_headers});

            if(api_get.ok) {
              let {discord: discord, foundry: foundry} = await api_get.json();
              discord ||= {}; foundry ||= {};

              logger.debug(`Looking for user in DB ${foundry.id}|${discord.id}|${discord.username}`);
              const [user] = await db.User.find({ $or: [{'_id': foundry.id}, {'discord.id': discord.id}, {'name': discord.username}] });

              if (user && user.role > 0) {
                logger.debug('Updating API with Foundry user data');
                const api_patch = await fetch(api_url, {
                  method: 'patch',
                  headers: api_headers,
                  body: JSON.stringify({foundry: user})
                });

                if(!api_patch.ok) {
                  logger.warn(`Failed to update API with user data: ${api_patch.status} - ${await api_patch.text()}`)
                }

                sessions.logoutWorld(req, resp);
                const session = sessions.getOrCreate(req, resp);
                session.worlds[game.world.id] = user.id;

                extensibleFoundry.hooks.call('audit.user.login', req, session, user);
                logger.info('User authentication successful for user ' + user.name, {
                  session: session.id,
                  ip: req.ip
                });

                if(req.path.startsWith('/join')) {
                  resp.redirect('/game');
                }
              }
            }
          } catch (e) {
            logger.warn(`Could not login with JWT: ${e.message}`)
          }
        }
      }

    }
  }

  async route_oauth_authenticate(req, resp) {
    const {game} = global;

    if(req.params.service === 'jwt') {

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

      resp.render('jwt_authenticate', {
        bodyClass: "vtt players",
        scripts: scripts,
        styles: styles
      });
    }
  }
}
