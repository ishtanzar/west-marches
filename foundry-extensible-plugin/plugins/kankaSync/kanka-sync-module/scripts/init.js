let _access_token;

class Kanka {

  static initialize() {
    const instance = new Kanka();

    instance.registerSettings();
    instance.setupHooks();
  }

  async validateToken(access_token, refresh_token) {
    const userResult = await fetch('https://kanka.io/api/1.0/profile', {
      headers: {
        authorization: `Bearer ${_access_token}`,
      },
    });

    if(userResult.ok) {
      return true;
    }

    if(userResult.status === 401) {
      //TODO: refresh token
    } else if(userResult.status >= 400) {
      //TODO error
    }

    return false;
  }

  setupHooks() {
    Hooks.once('ready', async () => {
      const user = game.users.current;
      _access_token = user.data.auth.kanka.access_token;
      const _refresh_token = user.data.auth.kanka.refresh_token;

      if(_access_token && await this.validateToken(_access_token, _refresh_token)) {
        //TODO
      } else {
        await this.sendLoginMessage();
      }
    });

    Hooks.on('kanka-oauth', async (access_token, popup_window) => {
      _access_token = access_token;
      popup_window.close();
    });

  }

  async sendLoginMessage() {
    const chatMessage = new ChatMessage({
      speaker: {alias: ame.i18n.localize("KankaSync.Chat.LoginMessage.Title")},
      content: `<p>${game.i18n.localize("KankaSync.Chat.LoginMessage.Content.1")}</p>` +
        '<div>' +
        '    <button id="kanka-join">' +
        `        ${game.i18n.localize("KankaSync.Chat.LoginMessage.Button.Join")}` +
        '    </button>' +
        '</div>' +
        `<p>${game.i18n.localize("KankaSync.Chat.LoginMessage.Content.2")}</p>` +
        '<div>' +
        '    <button id="kanka-login">' +
        '        <img alt="kanka icon" src="modules/kankaSync/images/kanka.png" style="border: 0; width: auto; height: 1em; vertical-align: middle;"/>' +
        `        ${game.i18n.localize("KankaSync.Chat.LoginMessage.Button.Login")}` +
        '    </button>' +
        '</div>',
      whisper: [],
      timestamp: Date.now()
    });
    await ui.chat.postOne(chatMessage);

    $('#kanka-join').click( event => {
      event.preventDefault();
      window.open(
        game.settings.get('kanka-sync-module', 'url.invite'),
        '_blank'
      );
    });

    $('#kanka-login').click( event => {
      event.preventDefault();

      const width = 500;
      const height = 750;

      const screenLeft = window.screenLeft !== undefined ? window.screenLeft : window.screenX;
      const screenTop = window.screenTop !== undefined ? window.screenTop : window.screenY;
      const screenWidth = window.innerWidth ? window.innerWidth : document.documentElement.clientWidth ? document.documentElement.clientWidth : screen.width;
      const screenHeight = window.innerHeight ? window.innerHeight : document.documentElement.clientHeight ? document.documentElement.clientHeight : screen.height;

      const left = (screenWidth - width) / 2 + screenLeft
      const top = (screenHeight - height) / 2 + screenTop

      const redirect_uri = game.settings.get('kanka-sync-module', 'oauth.redirectUri');
      const client_id = game.settings.get('kanka-sync-module', 'oauth.clientId');

      window.open(
        `https://kanka.io/oauth/authorize?client_id=${client_id}&redirect_uri=${redirect_uri}&response_type=code`,
        "Authorization",
        `width=${width},height=${height},top=${top},left=${left}`);
    });
  }

  registerSettings() {
    const settings = [
      {
        name: 'KankaSync.Settings.KankaClientId.Name',
        value: 'oauth.clientId',
      },
      {
        name: 'KankaSync.Settings.kankaClientSecret.Name',
        value: 'oauth.clientSecret'
      },
      {
        name: 'KankaSync.Settings.kankaRedirectUri.Name',
        value: 'oauth.redirectUri',
        default: 'http://localhost:30000/oauth/authenticate/kanka'
      },
      {
        name: 'KankaSync.Settings.JoinUrl.Name',
        value: 'url.invite',
      },
    ];

    Hooks.once('init', async () => {
      settings.map(item => {
        game.settings.register('kanka-sync-module', item.value, {
          name: item.name,
          scope: 'world',
          config: true,
          type: String,
          default: item.default ? item.default : ''
        });
      });
    });
  }
}

Kanka.initialize();
