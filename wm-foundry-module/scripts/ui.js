
function selectGroup() {
  let $dropdown = $('<select id="group_tp_id"></select>');

  //TODO: Add setting for folder selection
  //CIlYFrkfmjt42rWA
  for (const actor of game.folders.find(folder => folder.id === "SLBsewQBhjQMKyZ2").children) {
    $dropdown.append($('<option value="{{value}}">{{title}}</option>'
      .replace(/{{value}}/g, actor.id)
      .replace(/{{title}}/g, actor.name)));
  }

  return $dropdown[0].outerHTML;
}

function dialogGroupTeleport() {
  let d = new Dialog({
    title: game.i18n.localize('WestMarches.Group_Teleport.Dialog.Title'),
    content: selectGroup(),
    buttons: {
      ok: {
        icon: '<i class="fas fa-check"></i>',
        label: game.i18n.localize('WestMarches.Group_Teleport.Dialog.Buttons.Ok'),
        callback: $html => {
          for (const actor of game.folders.find(folder => folder.id === $html.find('#group_tp_id :selected').val()).content) {
            let player = game.users.find(user => {
              if(user.character) {
                return user.character.id === actor.id
              }
              return false;
            });
            if(player) {
              console.log("WestMarches | Pulling " + player.name);
              game.socket.emit("pullToScene", game.users.current.viewedScene, player.id);
            }
          }
        }
      }
    }
  });

  d.render(true)
}

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

export {PlayerJournal, dialogGroupTeleport};
