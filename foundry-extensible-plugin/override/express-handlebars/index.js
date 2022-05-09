"use strict";

const original = require('express-handlebars');

function exphbs (config) {
  const {extensibleFoundry} = global;

  extensibleFoundry.hooks.call('pre.express-handlebars.config', config);
  return original(config);
}

exports = module.exports = exphbs;
exports.create = original.create;
exports.ExpressHandlebars = original.ExpressHandlebars;
