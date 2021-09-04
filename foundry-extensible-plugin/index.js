'use strict';

const path = require('path');
const overrideRequire = require('override-require');

class RequireOverride {
  static _path = path.join(__dirname, 'override');
  static _overrides = {
    '^init$': 'init',
    '^\..*\/express$': 'express',
    '^\..*\/views': 'views',
    '^\..*\/world': 'world',
    '^\..*\/entities/user': 'user',
  };

  static add_overrides(overrides) {
    for(let override of overrides) {
      this._overrides[override.pattern] = override.override;
    }
  }

  static get overrides() {
    return this._overrides;
  }

  static check(request, parent) {
    return parent && ![__dirname, RequireOverride._path].includes(parent.path) &&
      !parent.path.match(/node_modules/) &&
      Object.keys(RequireOverride.overrides).find(override => RequireOverride.isOverrideRequestMatch(request, override));
  }

  static resolve(request, parent) {
    return require(path.join(RequireOverride._path, Object.entries(RequireOverride.overrides)
      .find(override => RequireOverride.isOverrideRequestMatch(request, override.shift())).pop()));
  }

  static isOverrideRequestMatch(request, override) {
    return request.match(RegExp(override))
  }
}

global.overrideRequire = RequireOverride;
overrideRequire(RequireOverride.check, RequireOverride.resolve);
