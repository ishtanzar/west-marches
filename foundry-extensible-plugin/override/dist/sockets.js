'use strict';

const {paths} = global;

const {activate, handleEvent} = require(paths.code + '/sockets');

async function new_activate(socket) {
  const {extensibleFoundry} = global;

  await extensibleFoundry.hooks.callAsync('pre.sockets.activate', socket);
  return await activate(socket);
}

module.exports = {'activate': new_activate, 'handleEvent': handleEvent};
