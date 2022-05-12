console.log("ExtensibleAuth Discord Client | Initialising");

function configureSettings() {
  game.settings.register("extensible-auth", "method.discord.enabled", {
    name: "ExtensibleAuth.Discord.Enabled.Name",
    scope: "world",
    default: false,
    type: Boolean,
    config: true
  });

  game.settings.register("extensible-auth", "method.discord.clientId", {
    name: "ExtensibleAuth.Discord.ClientId.Name",
    scope: "world",
    default: '',
    type: String,
    config: true
  });

  game.settings.register("extensible-auth", "method.discord.clientSecret", {
    name: "ExtensibleAuth.Discord.ClientSecret.Name",
    scope: "world",
    default: '',
    type: String,
    config: true
  });

  game.settings.register("extensible-auth", "method.discord.redirectUri", {
    name: "ExtensibleAuth.Discord.RedirectUri.Name",
    scope: "world",
    default: '',
    type: String,
    config: true
  });
}

if(game.settings) {
  configureSettings();
} else {
  Hooks.once('ready', configureSettings);
}
