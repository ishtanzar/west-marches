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

window.PlayerJournal= PlayerJournal;
