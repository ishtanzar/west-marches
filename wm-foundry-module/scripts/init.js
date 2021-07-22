console.log("WM | Loading PlayerJournal");

class PlayerJournal extends FormApplication {

  static get defaultOptions() {
    return mergeObject(super.defaultOptions, {
      id: "west-marches-player-journal-form",
      title: "Journal de Bord",
      template: "./modules/wm-player-journal/templates/journal.html",
      classes: ["player-journal"],
      height: 720,
      width: 800,
      resizable: true,
      submitOnClose: true,
      submitOnChange: true,
      closeOnSubmit: true
    });
  }

  async _updateObject(event, formData) {
    return this.object.update(formData);
  }
}

window.PlayerJournal = PlayerJournal;

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
    default: "http://localhost:30000/login/oauth"
  });
})
