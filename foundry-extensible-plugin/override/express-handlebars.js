"use strict";

const original = require('express-handlebars');
const path = require('path');

function exphbs (config) {
  const {extensibleFoundry} = global;

  extensibleFoundry.hooks.call('pre.express-handlebars.config', config);
  return original(config);
}


module.exports = exphbs;