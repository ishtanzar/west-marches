function getRecursiveFolders(parent) {
  const folders = [];

  for(const folder of (game.folders.filter(f => f.parent?.id === parent.id) || [])) {
    folders.push(folder);
    folders.push(...getRecursiveFolders(folder));
  }

  return folders;
}

function selectGroup() {
  let $dropdown = $('<select id="group_tp_id"></select>');

  for(const folder of getRecursiveFolders(game.folders.find(f => f.id === game.settings.get('wm-foundry-module', 'folders.groups')))) {
    $dropdown.append($('<option value="{{value}}">{{title}}</option>'
      .replace(/{{value}}/g, folder.id)
      .replace(/{{title}}/g, folder.name)));
  }

  return $dropdown[0].outerHTML;
}

function getUsersFromActorGroup(groupId) {
  const users = [];

  for (const actor of game.folders.find(folder => folder.id === groupId).content) {
    let player = game.users.find(user => {
      return user.character?.id === actor.id
    });
    if(player) {
      users.push(player);
    }
  }

  return users;
}

async function getUserFromKankaTag(tag) {
  const character = (await getCharacters()).find(c => c.id === tag);
  const actor = game.actors.find(a => a.name === character?.name);
  const ownerId = Object.keys(actor.data?.permission || []).find(userId => actor.data.permission[userId] === 3);
  return game.users.get(ownerId);
}

async function fetchEntities(type) {
  let apiResult, apiJson, entitiesResult = [], apiUrl = new URL(`https://kanka.io/api/1.0/campaigns/93396/${type}`);
  do {
    apiResult = await fetch(apiUrl.toString(), {
      headers: {
        authorization: `Bearer ${game.users.current.data.auth?.kanka?.access_token}`,
      },
    });
    apiJson = await apiResult.json();
    entitiesResult = entitiesResult.concat(apiJson.data);
    apiUrl = new URL(apiJson.links.next, apiUrl);
    apiUrl.protocol = 'https:';
  } while (apiJson.links.next)

  return entitiesResult;
}

async function getCharacters(refresh = false) {
  if(refresh || charactersCache.length === 0) {
    const allTags = await fetchEntities('tags');

    charactersCache = allTags
      .filter(tag => tag.type === 'PJ');
  }
  return charactersCache;
}

function dialogGroupTeleport() {
  const d = new Dialog({
    title: game.i18n.localize('WestMarches.Group_Teleport.Dialog.Title'),
    content: selectGroup(),
    buttons: {
      ok: {
        icon: '<i class="fas fa-check"></i>',
        label: game.i18n.localize('WestMarches.Group_Teleport.Dialog.Buttons.Ok'),
        callback: $html => {
          for(const user of getUsersFromActorGroup($html.find('#group_tp_id :selected').val())) {
            console.log("WestMarches | Pulling " + user.name);
            game.socket.emit("pullToScene", game.users.current.viewedScene, user.id);
          }
        }
      }
    }
  });

  d.render(true)
}

function dialogDismissGroup() {
  const d = new Dialog({
    title: game.i18n.localize('WestMarches.Session_Manager.Dialogs.Group_Select.Title'),
    content: selectGroup(),
    buttons: {
      ok: {
        icon: '<i class="fas fa-check"></i>',
        label: game.i18n.localize('WestMarches.Session_Manager.Dialogs.Group_Select.Buttons.Ok'),
        callback: async $html => {
          const baseFolderId = game.settings.get('wm-foundry-module', 'folders.pcs');
          const groupFolderId = $html.find('#group_tp_id :selected').val();
          const groupFolder = game.folders.find(folder => folder.id === groupFolderId);

          for (const actor of groupFolder.content) {
            await actor.update({
              folder: baseFolderId
            });
          }
          groupFolder.delete();
        }
      }
    }
  }).render(true);
}

function dialogDiscordSend(defaultMessage, data) {
  new Dialog({
    title: game.i18n.localize('WestMarches.Session_Manager.Dialogs.Message.Title'),
    content: `<textarea name="discord_message">${defaultMessage}</textarea>`,
    buttons: {
      ok: {
        icon: '<i class="fas fa-check"></i>',
        label: game.i18n.localize('WestMarches.Session_Manager.Dialogs.Message.Buttons.Ok'),
        callback: async $html => {
          const template = Handlebars.compile($html.find('textarea[name="discord_message"]').val(), {noEscape: true});
          game.socket.emit('discordSend',
            template(data),
            game.settings.get('wm-foundry-module', 'discord.channels.book'));
        }
      }
    }
  }).render(true);
}

async function dialogSelectGroup(actors) {
  const d = new Dialog({
    title: game.i18n.localize('WestMarches.Session_Manager.Dialogs.Group_Select.Title'),
    content: await renderTemplate('modules/wm-foundry-module/templates/new_session_group.hbs', {
      groups: game.folders.get(game.settings.get('wm-foundry-module', 'folders.groups')).children
    }),
    buttons: {
      ok: {
        icon: '<i class="fas fa-check"></i>',
        label: game.i18n.localize('WestMarches.Session_Manager.Dialogs.Group_Select.Buttons.Ok'),
        callback: async $html => {
          const newFolder = $html.find('input[name="group_name"]').val();
          let folderId = $html.find('select[name="group_id"] :selected').val();
          if(newFolder) {
            const folder = await Folder.create({
              name: newFolder,
              type: 'Actor',
              parent: game.settings.get('wm-foundry-module', 'folders.groups')
            });
            folderId = folder['_id'];
          }
          for(const actor of actors) {
            await actor.update({
              folder: folderId
            });
          }
          ui.notifications.info('Votre groupe est prêt !')
        }
      }
    }
  })

  d.render(true);
}

let charactersCache = [], sessionsCache = [];

class PlayerJournal extends FormApplication {

  static get defaultOptions() {
    return mergeObject(super.defaultOptions, {
      id: "west-marches-player-journal-form",
      title: "Journal de Bord",
      template: "./modules/wm-foundry-module/templates/journal.html",
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

class SessionForm extends FormApplication {

  constructor(entity) {
    super(mergeObject({
      tags: []
    }, entity));
  }

  static get defaultOptions() {
    return mergeObject(super.defaultOptions, {
      id: "west-marches-gm-session-edit",
      title: "Ma session",
      template: "./modules/wm-foundry-module/templates/session_edit.hbs",
      classes: ["session-editor"],
      dragDrop: [{callbacks: {drop: this._onDrop}}],
      height: 500,
      width: 850,
      resizable: true,
      closeOnSubmit: false
    });
  }

  async getData() {
    return {
      entity: mergeObject(duplicate(this.object), {
        actors: await Promise.all(this.object.tags.map(async tag => {
          const characterName = (await getCharacters()).find(c => c.id === tag);
          return await game.actors.find(a => a.name === characterName?.name);
        }))
      }),
    };
  }

  async _onDrop(event) {
    try {
      const dropData = JSON.parse(event.dataTransfer.getData('text/plain'));
      if(dropData.type === 'Actor') {
        const actor = game.actors.get(dropData.id);
        const character = (await getCharacters()).find(c => c.name === actor.name);
		   
		if(character == undefined){
		  ui.notifications.warn("Pas trouvé... Est-ce que le tag \"PJ\" a bien été ajouté sur Kanka?");
		}
        if(!this.object.tags.includes(character.id)) {
          this.object.tags.push(character.id);
        }
	   console.log(this.object);

        //TODO avoid the render
        this.render();
      }
    } catch (err) {
      console.warn(err);
    }
  }

  async getDiscordMessageData() {
    return {
      mention: `<@&${game.settings.get('wm-foundry-module', 'discord.mentions.organizers')}>`,
      players: await Promise.all(this.object.tags.map(async tag => {
        const owner = await getUserFromKankaTag(tag);
        const discordId = owner.data.discord?.id;
        return discordId ? `\n<@${discordId}>` : '';
      })),
      user: `<@${game.users.current.data.discord.id}>`
    }
  }

  async activateListeners(html) {
    await super.activateListeners(html);

    html.on('click', 'button[data-action]', async event => {
      const {action} = event.currentTarget?.dataset ?? {};
      switch(action) {
        case 'book':
          dialogDiscordSend(
            game.settings.get('wm-foundry-module', 'discord.messages.book'),
            await this.getDiscordMessageData()
          );
          break;
        case 'free':
          dialogDiscordSend(
            game.settings.get('wm-foundry-module', 'discord.messages.release'),
            await this.getDiscordMessageData()
          );
          break;
        case 'end':
          dialogDismissGroup();
          break;
        case 'start':
          await dialogSelectGroup(await Promise.all(this.object.tags.map(async tag => {
            const character = (await getCharacters()).find(c => c.id === tag);
            if(character) {
              return await game.actors.find(a => a.name === character.name);
            }
          })));
          break;
	   case 'removechar':
	   
		const character = (await getCharacters()).find(c => c.name === event.currentTarget.dataset.value);
		if(character) {
			this.object.tags.splice(this.object.tags.indexOf(character.id), 1);
		}
		this.render(true);
	     break;
      }
    });
  }

  async _updateObject(event, formData) {
    const app = this;
    this.object = mergeObject(this.object, formData);

    game.socket.emit('createOrUpdateGameSession', {
      id: this.object.id,
      name: this.object.name,
      date: this.object.date,
      content: this.object.content,
      type: 'Rapport',
      tags: this.object.tags
    }, response => {
      if(response.ok) {
        ui.notifications.info('Rapport enregistré.')
        app.object.id = response.entity.id;
      } else {
        ui.notifications.error('Erreur lors de l\'enregistrement du rapport.')
        console.warn(response);
      }
    });
  }
}

class SessionManager extends Application {
  static get defaultOptions() {
    return mergeObject(super.defaultOptions, {
      id: "west-marches-gm-session-manager",
      title: "Mes Sessions",
      template: "./modules/wm-foundry-module/templates/session_list.hbs",
      classes: ["session-manager"],
      height: 470,
      width: 400,
      resizable: false,
    });
  }

  async getSessions(refresh = false) {
    if(sessionsCache.length === 0 || refresh) {
      const allJournals = await fetchEntities('journals');

      sessionsCache = allJournals
        .filter(journal => journal.type === 'Rapport')
        .sort((a, b) => {
          return new Date(b.date) - new Date(a.date)
        });
    }
    return sessionsCache;
  }

  async _render(force, options) {
    await super._render(force, options);

    this.getSessions().then(sessions => {
      const template = Handlebars.compile('{{#each sessions}}<li class="session_item" data-kanka-id="{{this.id}}">{{this.name}}</li>{{/each}}');
      $(this.element).find('#session_list').html(template({sessions: sessions}));
      $(this.element).find('#session_list .session_item').on('click', async event => {
        event.preventDefault();
        ui.notifications.info('Chargement de la session, veuillez patienter...')
        const session = sessions.find(s => s.id === $(event.target).data('kanka-id'));
        const form = new SessionForm({
          id: session.id,
          name: session.name,
          date: session.date,
          // game_date: '',
          // game_duration: '',
          content: session.entry,
          tags: session.tags || []
        }).render(true);
      });
    })
  }

  // filterList(filter) {
  //   if (!filter) {
  //     // this.resetFilter();
  //     return;
  //   }
  //
  //   $(this.element).find('.session_item').each((_, element) => {
  //
  //   });
  // }

  async activateListeners(html) {
    await super.activateListeners(html);

    html.on('input', '[name="filter"]', event => {
      const filter = event?.target?.value ?? '';

      if (!filter.trim().length) {
        // this.resetFilter();
        return;
      }

      // this.filterList(filter);
    });

    html.on('click', 'button#session_new', event => {
      new SessionForm().render(true);
    });
  }

}

export {PlayerJournal, SessionManager, dialogGroupTeleport};
