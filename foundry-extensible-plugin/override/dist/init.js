'use strict';

const path = require('path');
let logger;

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
    logger.debug(`Registered callback for ${hook} hook`);
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
    logger.debug(`Calling ${hook} hook with args: ${args}`);
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
    logger.debug(`Calling ${hook} hook with args: ${args}`);
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
    logger.debug(`Calling ${hook} hook with args: ${args}`);
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
      logger.error(`Error thrown in hooked function ${fn.name}: ${err}`);
    }
  }
}

class ExtensibleFoundryPlugin {

  static _plugins = []
  static _instance;

  static initialize(pluginsPath) {
    logger.info('ExtensibleFoundry init');

    this._instance = global.extensibleFoundry = new ExtensibleFoundryPlugin();
    const {overrideRequire} = global;

    // TODO: dynamic plugin list
    for(let plugin of ['api', 'metrics', 'extensibleAuth', 'extensibleAuthDiscord', 'extensibleAuthJwt']) {
      const cls = require(path.join(pluginsPath, plugin, 'main'));
      this._plugins.push(new cls(this._instance));
    }

    const entities = [];
    this._instance.hooks.call('setup_entities', entities);
    overrideRequire.add_overrides(entities);
  }

  get hooks() {
    return Hooks;
  }

}

function initialize(argv, paths, startupMessages) {
  const foundry_init = require(path.join(paths.code, 'init'));
  const createVTTLogger = require(path.join(paths.code, 'logging'));

  logger = createVTTLogger(paths, []);

  //TODO: configuration file
  ExtensibleFoundryPlugin.initialize(path.join('..', '..', 'plugins'));
  foundry_init(argv, paths, startupMessages);
}

module.exports = initialize;