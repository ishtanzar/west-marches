import path from "path";
import url from "url";
import Module from "foundry:dist/packages/module.mjs";

export default class ExtensibleAuthFoundryPlugin {

  static MODULE_NAME = 'extensibleAuth';

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    this._pluginRoot = path.dirname(url.fileURLToPath(import.meta.url));
    this._base = base;
    this._methods = [{
      id: 'access_key',
      name: this.constructor.MODULE_NAME,
      title: 'ExtensibleAuth Plugin',
      esmodules: [
        'modules/main.mjs'
      ],
      languages: [
        { lang: "en", name: "English", path: "languages/en.json" }
      ],
      path: this._pluginRoot
    }];

    base.hooks.on('post.views.join.getStaticContent', this.getStaticContent);
    base.hooks.on('extensiblePlugins.clientModules.register', this.registerClientModules.bind(this));
    base.hooks.on('extensiblePlugins.migrate', this.migrate.bind(this));
    base.hooks.on('post.express.middleware', this.middleware.bind(this));
    base.hooks.on('pre.express.staticFiles', this.staticFiles.bind(this));
    base.hooks.on('post.express.listen', this.listen.bind(this));

    base.hooks.on('post.extensiblePlugin.loadPlugins', async () => {
      await base.hooks.callAsync('extensibleAuth.method.register', this.registerMethod.bind(this));
    });
  }

  async registerClientModules() {
    this._methods.forEach(method => {
      this._base.addTemplateDirectory(method.path);
      this._base.addViewsDirectory(path.join(method.path, 'templates', 'views'));

      this._base.addClientModule(new Module({
        name: method.name,
        title: method.title,
        scripts: method.scripts,
        esmodules: method.esmodules,
        path: method.path,
        languages: method.languages,
        flags: {
          webRoot: path.join(method.path, 'public'),
          webPrefix: `/modules/${method.name}/`
        }
      }));
    });
  }

  staticFiles() {
    this._methods.forEach(method => {
      this._base.addStaticFilesDirectory(path.join(method.path, 'public'), `/modules/${method.name}/`);
    });
  }

  async listen(express) {
    const authPlugin = this;

    express.io.on('connection', socket => {
      socket.on('getLoginData', authPlugin.getLoginData.bind(this));
    })
  }

  async getLoginData(resolve) {
    const {db} = global;

    const enabled_methods = (await db.Setting.find({'key': new RegExp(`^${this.constructor.MODULE_NAME}\.method\..*\.enabled$`), value: 'true'})).map(e => e.key);
    const methods = this._methods
        .reduce((filtered, m) => {
          if(enabled_methods.includes(`${this.constructor.MODULE_NAME}.method.${m.id}.enabled`)) {
            filtered.push(m.id)
          }
          return filtered;
        }, []);

    const data = {
      methods: methods.length > 0 ? methods : ['access_key']
    };
    await global.extensibleFoundry.hooks.callAsync('post.extensibleAuth.getLoginData', data);
    resolve(data);
  }

  getStaticContent(opts) {
    opts.result.scripts.push({src: 'modules/extensibleAuth/scripts/join.js', type: 'script', priority: 0, isModule: false});
  }

  middleware(router) {
    router.get('/oauth/authenticate/:service', this.route_oauth_authenticate);
  }

  async route_oauth_authenticate(req, resp) {
    global.extensibleFoundry.hooks.call('extensibleAuth.route_oauth_authenticate', req, resp);
  }

  registerMethod(opts) {
    this._methods.push(opts);
  }

  async migrate() {
    let enabled = false, migrated = false;
    for(let setting of await db.Setting.find({key: /extensible-auth.*access_key/})) {
      migrated = true;
      enabled = enabled || setting.value;
      await setting.delete();
    }
    if(migrated) {
      await db.Setting.set(`${this.constructor.MODULE_NAME}.method.access_key.enabled`, enabled);
    }
  }

}
