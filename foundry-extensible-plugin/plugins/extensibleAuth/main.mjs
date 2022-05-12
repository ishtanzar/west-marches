import path from "path";
import url from "url";
import Module from "foundry:dist/packages/module.mjs";

export default class ExtensibleAuthFoundryPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    this._pluginRoot = path.dirname(url.fileURLToPath(import.meta.url));
    this._base = base;
    this._methods = [{
      id: 'access_key',
      module_name: 'extensible-auth-access_key-client',
      title: 'ExtensibleAuth Password Plugin',
      scripts: [],
      languages: [
        { lang: "en", name: "English", path: "languages/en.json" }
      ],
      root: path.join(this._pluginRoot)
    }];

    base.addTemplateDirectory(this._pluginRoot);
    base.addStaticFilesDirectory(path.join(this._pluginRoot, 'public'));

    base.hooks.on('post.express.CORE_VIEW_SCRIPTS', this.viewScripts);
    base.hooks.on('pre.express.staticFiles', this.staticFiles.bind(this));
    base.hooks.on('pre.express.defineRoutes', this.defineRoutes.bind(this));
    base.hooks.on('post.initialize', this.post_initialize.bind(this));
  }

  viewScripts(modules) {
    modules.push('scripts/extensibleAuth.js');
  }

  staticFiles(router) {
    this._base.hooks.call('extensibleAuth.register_method', this.register_method.bind(this));

    this._methods.forEach(method => {
      const modulePath = path.join('modules', method.module_name);
      this._base.addStaticFilesDirectory(path.join(method.root, modulePath), '/' + modulePath);
      this._base.addClientModule(new Module({
        name: method.module_name,
        title: method.title,
        scripts: method.scripts,
        root: method.root,
        languages: method.languages
      }));
    });
  }

  defineRoutes(router) {
    router.get('/oauth/authenticate/:service', this.route_oauth_authenticate);
  }

  async post_initialize() {
    const settingName = 'core.moduleConfiguration', {db} = global;
    const [moduleConfigSetting] = (await db.Setting.dump()).filter(s => s.key === 'core.moduleConfiguration')
    const authAccessKeyModuleSetting = {
      "extensible-auth-access_key-client": true
    };

    await db.Setting.set(settingName, Object.assign(await db.Setting.getValue(settingName), authAccessKeyModuleSetting));

    this._base.hooks.on('pre.setting.save', async (setting) => {
      if(setting.id === moduleConfigSetting['_id']) {
        setting.data.update({value: JSON.stringify(Object.assign(setting.value, authAccessKeyModuleSetting))});
      }
    });
  }

  async route_oauth_authenticate(req, resp) {
    global.extensibleFoundry.hooks.call('extensibleAuth.route_oauth_authenticate', req, resp);
  }

  register_method(opts) {
    this._methods.push(opts);
  }

}
