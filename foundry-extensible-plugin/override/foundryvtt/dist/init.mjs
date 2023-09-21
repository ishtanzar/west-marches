import path from "path";
import fs from "fs";
import express from "express";
import os from "os";

/**
 * A simple event framework used throughout Foundry Virtual Tabletop.
 * When key actions or events occur, a "hook" is defined where user-defined callback functions can execute.
 * This class manages the registration and execution of hooked callback functions.
 */
class Hooks {

  static _hooks = {};
  static _once = [];
  static _ids = [];
  static _id = 1;

  /**
   * Register a callback handler which should be triggered when a hook is triggered.
   *
   * @param {string} hook   The unique name of the hooked event
   * @param {Function} fn   The callback function which should be triggered when the hook event occurs
   * @return {number}       An ID number of the hooked function which can be used to turn off the hook later
   */
  static on(hook, fn) {
    global.extensibleLogger.debug(`Registered callback for ${hook} hook`);
    const id = this._id++;
    this._hooks[hook] = this._hooks[hook] || [];
    this._hooks[hook].push(fn);
    this._ids[id] = fn;
    return id;
  }

  /* -------------------------------------------- */

  /**
   * Register a callback handler for an event which is only triggered once the first time the event occurs.
   * After a "once" hook is triggered the hook is automatically removed.
   *
   * @param {string} hook   The unique name of the hooked event
   * @param {Function} fn   The callback function which should be triggered when the hook event occurs
   * @return {number}       An ID number of the hooked function which can be used to turn off the hook later
   */
  static once(hook, fn) {
    this._once.push(fn);
    return this.on(hook, fn);
  }

  /* -------------------------------------------- */

  /**
   * Unregister a callback handler for a particular hook event
   *
   * @param {string} hook           The unique name of the hooked event
   * @param {Function|number} fn    The function, or ID number for the function, that should be turned off
   */
  static off(hook, fn) {
    if ( typeof fn === "number" ) {
      let id = fn;
      fn = this._ids[fn];
      delete this._ids[id];
    }
    if ( !this._hooks.hasOwnProperty(hook) ) return;
    const fns = this._hooks[hook];
    let idx = fns.indexOf(fn);
    if ( idx !== -1 ) fns.splice(idx, 1);
    logger.debug(`Unregistered callback for ${hook} hook`);
  }

  /* -------------------------------------------- */

  /**
   * Call all hook listeners in the order in which they were registered
   * Hooks called this way can not be handled by returning false and will always trigger every hook callback.
   *
   * @param {string} hook   The hook being triggered
   * @param {...*} args     Arguments passed to the hook callback functions
   */
  static callAll(hook, ...args) {
    global.extensibleLogger.debug(`Calling ${hook} hook with args: ${args}`);
    if ( !this._hooks.hasOwnProperty(hook) ) return;
    const fns = new Array(...this._hooks[hook]);
    for ( let fn of fns ) {
      this._call(hook, fn, args);
    }
    return true;
  }

  /* -------------------------------------------- */

  /**
   * Call hook listeners in the order in which they were registered.
   * Continue calling hooks until either all have been called or one returns `false`.
   *
   * Hook listeners which return `false` denote that the original event has been adequately handled and no further
   * hooks should be called.
   *
   * @param {string} hook   The hook being triggered
   * @param {...*} args      Arguments passed to the hook callback functions
   */
  static call(hook, ...args) {
    global.extensibleLogger.debug(`Calling ${hook} hook with args: ${args}`);
    if ( !this._hooks.hasOwnProperty(hook) ) return;
    const fns = new Array(...this._hooks[hook]);
    for ( let fn of fns ) {
      let callAdditional = this._call(hook, fn, args);
      if ( callAdditional === false ) return false;
    }
    return true;
  }

  /**
   * Call hook listeners in the order in which they were registered.
   * Continue calling hooks until either all have been called or one returns `false`.
   *
   * Hook listeners which return `false` denote that the original event has been adequately handled and no further
   * hooks should be called.
   *
   * @param {string} hook   The hook being triggered
   * @param {...*} args      Arguments passed to the hook callback functions
   */
  static async callAsync(hook, ...args) {
    global.extensibleLogger.debug(`Calling ${hook} hook with args: ${args}`);
    if ( !this._hooks.hasOwnProperty(hook) ) return;
    const fns = new Array(...this._hooks[hook]);
    for ( let fn of fns ) {
      let callAdditional = await this._call(hook, fn, args);
      if ( callAdditional === false ) return false;
    }
    return true;
  }

  /* -------------------------------------------- */

  /**
   * Call a hooked function using provided arguments and perhaps unregister it.
   * @private
   */
  static _call(hook, fn, args) {
    if ( this._once.includes(fn) ) this.off(hook, fn);
    try {
      return fn(...args);
    } catch(err) {
      global.extensibleLogger.error(`Error thrown in hooked function ${fn.name}: ${err}`);
    }
  }
}

class ExtensibleFoundryPlugin {
  static _instance;

  _plugins = [];
  _templatePath = [];
  _staticPath = [];
  _viewsPath = [];
  _clientModules = [];

  constructor(extensibleConfig) {
    this.hooks.on('pre.setting.save', this.preSettingSave.bind(this));
    this.hooks.on('post.files.loadTemplate', this.loadTemplate.bind(this));
    this.hooks.on('post.world.modules', this.getModules.bind(this));
    this.hooks.on('post.world.setup', this.postWorldSetup.bind(this));
    this.hooks.on('extensiblePlugins.clientModules.register', this.registerClientModule.bind(this));
    this.hooks.on('post.initialize', this.postInitialize.bind(this));

    this._config = extensibleConfig;

    this.addStaticFilesDirectory(path.join(global.extensiblePluginRoot, 'public'), '/modules/foundry-extensible-plugin/');
  }

  static async initialize(extensibleConfig) {
    global.extensibleLogger.info('ExtensibleFoundry init');

    this._instance = global.extensibleFoundry = new ExtensibleFoundryPlugin(extensibleConfig);
    await this._instance.loadPlugins();
  }

  get hooks() {
    return Hooks;
  }

  async loadPlugins() {
    for(let pluginId of this._config.plugins || []) {
      const plugin = await import(path.join(this._config.pluginsPath, pluginId, 'main.mjs'))
      this._plugins.push(new plugin.default(this));
    }
    await this.hooks.callAsync('post.extensiblePlugin.loadPlugins');
  }

  addTemplateDirectory(dir) {
    this._templatePath.push(dir);
  }

  addStaticFilesDirectory(path, prefix = '/') {
    this._staticPath.push({
      prefix: prefix,
      path: path
    });
  }

  addClientModule(module) {
    this._clientModules.push(module);
  }

  addViewsDirectory(dir) {
    this._viewsPath.push(dir);
  }

  loadTemplate(relative, template) {
    for(let templateRoot of this._templatePath) {
      const absolute = path.join(templateRoot, relative);

      if(fs.existsSync(absolute)) {
        Object.assign(template, delete template['error'], {
          html: fs.readFileSync(absolute, {encoding: "utf8"}),
          success: true
        });
      }
    }
  }

  getModules(modules) {
    this._clientModules.forEach(module => {
      if (modules.filter(pkg => pkg.id === module.id).length === 0) {
        modules.push(module);
      }
    });
  }

  async postWorldSetup() {
    await extensibleFoundry.hooks.callAsync('extensiblePlugins.migrate');
    await extensibleFoundry.hooks.callAsync('extensiblePlugins.clientModules.register');

    const app = global.config.express.app;

    for(let viewsRoot of this._viewsPath) {
      app.set('views', [viewsRoot].concat(app.get('views')));
    }

    for(let entry of this._staticPath) {
      app.use(entry.prefix, express.static(entry.path));
    }
  }

  async registerClientModule() {
    const { default: Module } = await import("foundry:dist/packages/module.mjs");

    this.addClientModule(new Module({
      name: 'foundry-extensible-plugin',
      title: 'Foundry Extensible Plugin',
      minimumCoreVersion: global.release.generation,
      compatibleCoreVersion: global.release.generation,
      path: global.extensiblePluginRoot
    }));
  }

  async postInitialize() {
    const {db} = global, settingName = 'core.moduleConfiguration';

    const setting = await db.Setting.getValue(settingName);
    for(let module of this._clientModules) {
      setting[module.id] = true;
    }
    await db.Setting.set(settingName, setting);
  }

  async preSettingSave(setting) {
    const settingName = 'core.moduleConfiguration';

    if(setting.key === settingName) {
      for(let module of this._clientModules) {
        setting.value[module.id] = true;
      }

      setting.data.update({value: JSON.stringify(setting.value)});
    }
  }

}

export default async function initialize({args: args = [], root: root, messages: messages = [], debug: debug = false} = {}) {
  global.foundryRoot = root;

  const init = await import('foundry:dist/init.mjs');

  let extensibleConfigPath = '/home/foundry/resources/extensible-config.json';
  let extensibleConfig = {
    'pluginsPath': new URL('/home/foundry/resources/foundry-extensible-plugin/plugins', import.meta.url).pathname,
    'plugins': ['api', 'accessLogs']
  };

  for(let arg of args) {
    if(/^--extensible-config/.test(arg)) {
      extensibleConfigPath = arg.split('=')[1];
    }
  }
  messages.push({level: 'info', message: 'ExtensiblePlugin config path: ' + extensibleConfigPath});

  if(fs.existsSync(extensibleConfigPath)) {
    extensibleConfig = Object.assign(extensibleConfig, JSON.parse(fs.readFileSync(extensibleConfigPath, "utf8")));
  }

  messages.push({level: 'info', message: 'ExtensiblePlugin config: \n' + JSON.stringify(extensibleConfig, null, 2)})


  await ExtensibleFoundryPlugin.initialize(extensibleConfig);
  await init.default({
    args: args,
    root: root,
    messages: messages,
    debug: debug
  });
  await extensibleFoundry.hooks.callAsync('post.initialize');
}
