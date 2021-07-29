function registerSettings() {
  Hooks.once('init', async function () {
    game.settings.register("wm-foundry-module", "oauthClientId", {
      name: 'WestMarches.Settings.OAuthClientId.Name',
      scope: 'world',
      config: true,
      type: String,
      default: ""
    });

    game.settings.register("wm-foundry-module", "oauthClientSecret", {
      name: 'WestMarches.Settings.OAuthClientSecret.Name',
      scope: 'world',
      config: true,
      type: String,
      default: ""
    });

    game.settings.register("wm-foundry-module", "oauthRedirectUri", {
      name: 'WestMarches.Settings.OAuthRedirectUri.Name',
      scope: 'world',
      config: true,
      type: String,
      default: "http://localhost:30000/login/discord"
    });
  });
}

export {registerSettings};
