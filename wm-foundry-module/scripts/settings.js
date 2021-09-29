class Settings {

  static initialize() {
    Hooks.once('ready', () => {
      let actorsFolders = {};

      for (const folder of game.folders) {
        if (folder.type === 'Actor' && folder.data.parent == null) {
          actorsFolders[folder.data['_id']] = folder.data.name;
        }
      }

      game.settings.register('wm-foundry-module', 'folders.groups', {
        name: 'WestMarches.Settings.Folders.Groups.Name',
        scope: 'world',
        config: true,
        type: String,
        default: '',
        choices: actorsFolders
      });

      game.settings.register('wm-foundry-module', 'folders.pcs', {
        name: 'WestMarches.Settings.Folders.PCs.Name',
        scope: 'world',
        config: true,
        type: String,
        default: '',
        choices: actorsFolders
      });

      game.settings.register('wm-foundry-module', 'discord.token', {
        name: 'WestMarches.Settings.Discord.Token',
        scope: 'world',
        config: true,
        type: String,
        default: '',
      });

      game.settings.register('wm-foundry-module', 'discord.channels.book', {
        name: 'WestMarches.Settings.Discord.Channels.Book',
        scope: 'world',
        config: true,
        type: String,
        default: '',
      });

      game.settings.register('wm-foundry-module', 'discord.mentions.organizers', {
        name: 'WestMarches.Settings.Discord.Mentions.Organizers',
        scope: 'world',
        config: true,
        type: String,
        default: '',
      });

      game.settings.register('wm-foundry-module', 'discord.messages.book', {
        name: 'WestMarches.Settings.Discord.Messages.Book',
        scope: 'world',
        config: true,
        type: String,
        default: 'Bonsoir chers {{mention}}, {{user}} aurait besoin d\'une table pour : {{#each players}}{{this}}{{/each}}.\n Merci !',
      });

      game.settings.register('wm-foundry-module', 'discord.messages.release', {
        name: 'WestMarches.Settings.Discord.Messages.Release',
        scope: 'world',
        config: true,
        type: String,
        default: 'Bonsoir chers {{mention}}, {{user}} libère la table de : {{#each players}}{{this}}{{/each}}.\n Merci !',
      });

    });
  }

}

export {Settings};