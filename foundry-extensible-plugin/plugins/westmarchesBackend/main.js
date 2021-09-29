
const fetch = require('node-fetch');
const path = require("path");

async function discordSend(message, channel) {
  const {paths} = global;
  const {Setting} = require(path.join(paths.code, 'database', 'documents', 'settings'));
  const token = await Setting.get('wm-foundry-module.discord.token');

  const result = await fetch(`https://discord.com/api/channels/${channel}/messages`, {
    method: 'POST',
    body: new URLSearchParams({
      content: message
    }),
    headers: {
      authorization: `Bot ${token}`,
    },
  });
}

async function kankaSave(socket, entity, callback) {
  let method = 'POST', apiUrl = new URL('https://kanka.io/api/1.0/campaigns/67312/journals/');
  const {db, game} = global;
  const userId = socket.session.worlds[game.world.id];
  const currentUser = await db.User.findOne({'_id': userId});

  if(entity.id) {
    method = 'PUT';
    apiUrl = new URL(entity.id, apiUrl);
  }

  if(currentUser.auth && currentUser.auth.kanka) {
    const apiResult = await fetch(apiUrl.toString(), {
      method: method,
      body: JSON.stringify({
        name: entity.name,
        entry: entity.content,
        type: entity.type,
        date: entity.date,
        character_id: entity.author,
        tags: entity.tags
      }),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentUser.auth.kanka.access_token}`,
      },
    });
    const response = {
      ok: apiResult.ok,
      status: apiResult.status,
      entity: null
    }
    if(apiResult.ok) {
      const jsonResp = await apiResult.json();
      response.entity = jsonResp.data;
    } else {
      console.warn(apiResult);
    }
    await callback(response);
  } else {
    console.warn('No Kanka credentials');
  }
}

class WestMarchesBackendPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    base.hooks.on('pre.sockets.activate', async socket => {
      socket.on('discordSend', discordSend);
      socket.on('createOrUpdateGameSession', async (entity, callback) => await kankaSave(socket, entity, callback));
    });
  }

}

module.exports = WestMarchesBackendPlugin;