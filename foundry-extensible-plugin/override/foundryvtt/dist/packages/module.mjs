import Module from 'foundry:dist/packages/module.mjs';
import Files from 'foundry:dist/files/files.mjs';
import path from "path";

export default class ExtensibleModule extends Module {

  constructor(opts) {
    super(opts);

    if(opts.root) {
      this.path = path.join(opts.root, 'modules', this.id);
    }
  }

  _createData(data) {
    this._baseDir = data.root;

    return super._createData(data);
  }

  _getStaticFiles(scripts) {
    if (!scripts) return [];

    const e = [{
      root: global.paths.data,
      dirs: [path.join(this.constructor.collection, this.id)]
    }, {
      root: global.paths.public,
      dirs: ["scripts"]
    }];

    if(this._baseDir) {
      e.push({
        root: this._baseDir,
        dirs: [path.join('modules', this.id)]
      });
    }

    return Files.getStaticFiles(scripts, e, {allowHTTP: !0})
  }

  static getPackages({system: system} = {}) {
    const packages = Module.getPackages({system: system});
    extensibleFoundry.hooks.call('post.module.getPackages', packages);
    return packages;
  }

  static getCoreTranslationOptions() {
    const packages = Module.getCoreTranslationOptions();
    extensibleFoundry.hooks.call('post.module.getCoreTranslationOptions', packages);
    return packages;
  }

}
