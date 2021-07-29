
class Kanka {

  static initialize() {
    const instance = new Kanka();

    instance.registerSettings();
    instance.setupHooks();
  }

  setupHooks() {
    Hooks.once('ready', async () => {
      const refresh_token = localStorage.getItem('westmarches.kanka.refresh_token');

      if(refresh_token) {
        //TODO: refresh token
      }
    });

    Hooks.on('kanka-oauth', async (access_token, refresh_token, popup_window) => {
      localStorage.setItem('westmarches.kanka.access_token', access_token);
      localStorage.setItem('westmarches.kanka.refresh_token', refresh_token);
      popup_window.close();
    });

  }

  registerSettings() {
    const settings = [
      {
        name: 'WestMarches.Settings.KankaClientId.Name',
        value: "kankaClientId"
      },
      {
        name: 'WestMarches.Settings.kankaClientSecret.Name',
        value: "kankaClientSecret"
      },
      {
        name: 'WestMarches.Settings.kankaRedirectUri.Name',
        value: "kankaRedirectUri"
      },
    ];

    Hooks.once('init', async () => {
      settings.map(item => {
        game.settings.register("wm-foundry-module", item.value, {
          name: item.name,
          scope: 'world',
          config: true,
          type: String,
          default: ""
        });
      });
    });
  }
}

export {Kanka};

