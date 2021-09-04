console.log("ExtensibleAuth Plugin | Initialising");

Hooks.once('init', function () {
  fetch(getRoute('extensibleAuth/settings')).then(async resp => {
    const json = await resp.json();
    for (let setting of json.settings) {
      setting.type = window[setting.type];
      game.settings.register(setting.module, setting.key, setting);
    }
  });
});
