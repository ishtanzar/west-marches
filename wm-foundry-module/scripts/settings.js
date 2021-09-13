class Settings {

  static initialize() {
    Hooks.once('ready', () => {
      let actorsFolders = {};

      for (const folder of game.folders) {
        if (folder.type === 'Actor' && folder.data.parent == null) {
          actorsFolders[folder.data['_id']] = folder.data.name;
        }
      }

      game.settings.register('wm-foundry-module', 'groups.baseFolder', {
        name: 'WestMarches.Settings.Groups.BaseFolder.Name',
        scope: 'world',
        config: true,
        type: String,
        default: '',
        choices: actorsFolders
      });
    });
  }

}

export {Settings};