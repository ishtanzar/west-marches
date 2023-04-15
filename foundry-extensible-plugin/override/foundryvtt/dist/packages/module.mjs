import Module from 'foundry:dist/packages/module.mjs';
import Files from 'foundry:dist/files/files.mjs';
import LocalFileStorage from 'foundry:dist/files/local.mjs';
import path from "path";
import fs from "fs";

export default class ExtensibleModule extends Module {

  constructor(opts) {
    super(opts);

    if(opts.path) {
      this.path = opts.path;
    }
  }

  _createData(data) {
    this._baseDir = data.root;

    return super._createData(data);
  }

  _getStaticFiles(scripts) {
    const files = super._getStaticFiles(scripts);

    if(this.data.flags && this.data.flags.hasOwnProperty('webRoot')) {
      return files.concat(scripts.reduce((exists, script) => {
        const p = path.join(this.data.flags.webRoot, script);
        if (fs.existsSync(p)) {
          exists.push(path.join(this.data.flags.webPrefix || "", script))
        }
        return exists;
      }, []))
    }
    return files;
  }

  static getPackages({system: system, coreTranslation: coreTranslation = false} = {}) {
    const packages = Module.getPackages({system: system, coreTranslation: coreTranslation});
    extensibleFoundry.hooks.call('post.module.getPackages', packages);
    return packages;
  }

  static getCoreTranslationOptions() {
    const packages = Module.getCoreTranslationOptions();
    extensibleFoundry.hooks.call('post.module.getCoreTranslationOptions', packages);
    return packages;
  }

  static socketListeners(e) {
    extensibleFoundry.hooks.call('pre.module.socketListeners', e);
    Module.socketListeners(e);
    extensibleFoundry.hooks.call('post.module.socketListeners', e);
  }
}

