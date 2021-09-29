
import {PlayerJournal, dialogGroupTeleport, SessionManager} from "./ui.js";

class WestMarchesLayer extends CanvasLayer {

  static initialize() {
    const wmLayer = new WestMarchesLayer();

    Hooks.on('getSceneControlButtons', controls => {
      const isGM = game.user.isGM;
      const sessionManager = new SessionManager();
      wmLayer.deactivate();

      if(isGM) {
        canvas?.stage.addChild(wmLayer);
        controls.push({
            name: "westmarches",
            title: "WestMarches.Controls.Group",
            icon: "fas fa-map-marked-alt",
            layer: "WestMarchesLayer",
            visible: true,
            tools: [
              {
                name: "tp_group",
                title: "WestMarches.Controls.TP_Group",
                icon: "fas fa-directions fa-fw",
                button: true,
                onClick: dialogGroupTeleport
              },
              {
                name: "session_manager",
                title: "WestMarches.Controls.Sessions_Manager",
                icon: "fab fa-d-and-d",
                button: true,
                onClick: async => sessionManager.render(true)
              },
            ]
          });
      }

      if(game.user.character) {
        controls.find(g => g.name === "notes").tools?.push({
          name: "journal_wide",
          title: "WestMarches.Controls.Journal",
          icon: "fas fa-book-open",
          button: true,
          onClick: async () => new PlayerJournal(game.user.character).render(true)
        });
      }
    });
  }
}

export {WestMarchesLayer};
