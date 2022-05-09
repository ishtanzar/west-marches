

window.addEventListener("DOMContentLoaded", async function() {
  const _originalJoinGameForm = JoinGameForm;

  class ExtensibleJoinGameForm extends _originalJoinGameForm {

    _authMethods = ['access_key'];

    constructor(object, options) {
      super(object, options);
      //TODO: check enabled methods in settings
    }

    getData(options) {
      const data = super.getData(options);
      data.auth_methods = this._authMethods;
      return data;
    }

    async _renderInner(data) {
      data.auth_methods = await Promise.all(this._authMethods.map(method => {
        return renderTemplate(`templates/auth/${method}.html`, data);
      }));

      return super._renderInner(data);
    }
  }

  JoinGameForm = ExtensibleJoinGameForm;

  console.log(`ExtensibleAuthPlugin | Loaded`);
});

