
class ExtensibleAuth {

  static async init() {
    game.settings.register("extensibleAuth", "method.access_key.enabled", {
      name: "ExtensibleAuth.AccessKey.Enabled.Name",
      scope: "world",
      default: true,
      type: Boolean,
      config: true
    });

    console.log(`ExtensibleAuthPlugin | Initialized`);
  }

}

if(typeof Hooks !== 'undefined') {
  Hooks.once('init', async function() {
    await ExtensibleAuth.init();
  });
}
