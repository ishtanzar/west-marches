'use strict';

const {paths} = global;
const auth = require(paths.code + '/auth');
const original = auth.sessions.authenticateUser;

async function authenticateUser(req, resp) {
  const {extensibleFoundry} = global;
  const result = original.bind(auth.sessions)(req, resp);

  await extensibleFoundry.hooks.callAsync('post.auth.authenticateUser', req, resp, result);
  return result;
}

auth.sessions.authenticateUser = authenticateUser;

module.exports = auth;