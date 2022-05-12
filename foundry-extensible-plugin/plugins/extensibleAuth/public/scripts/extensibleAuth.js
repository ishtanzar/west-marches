
const loadScript = src => {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.onload = resolve
    script.onerror = reject
    script.src = src
    document.head.append(script)
  })
}

window.addEventListener("DOMContentLoaded", async function() {
  // Get the current URL
  const url = new URL(window.location.href);
  const view = url.pathname.split("/").pop();

  if(typeof Hooks !== 'undefined') {
    Hooks.once('post.game.registerSettings', game => {
      game.settings.register("extensible-auth", "method.access_key.enabled", {
        name: "ExtensibleAuth.AccessKey.Enabled.Name",
        scope: "world",
        default: true,
        type: Boolean,
        config: true
      });

      if(view === 'join')  {
        const moduleConfig = game.settings.get('core', 'moduleConfiguration');
        Object.keys(moduleConfig).forEach(id => {
          if(id.startsWith('extensible-auth') && moduleConfig[id]) {
            (async () => loadScript(`modules/${id}/scripts/init.js`))();
          }
        });
      }
    });
  }

  if (typeof JoinGameForm !== 'undefined') {
    const _JoinGameForm = JoinGameForm;

    class ExtensibleJoinGameForm extends _JoinGameForm {

      get _authMethods() {
        const methods = Array.from(game.settings.settings.keys())
          .filter(i => {
            if (i.match(/extensible-auth.method.*.enabled/)) {
              return game.settings.get('extensible-auth', i.substring(16));
            }
            return false;
          })
          .map(i => i.split('.')[2]);
        return methods.length > 0 ? methods : ['access_key'];
      }

      constructor(object, options) {
        super(object, options);
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
  }

  if(typeof Setup !== 'undefined') {
    const _Setup = Setup;

    class ExtensibleSetup extends _Setup {
      registerSettings() {
        super.registerSettings();
        // Since the class replacement occurs after the extends, we need the hook twice
        Hooks.call('post.game.registerSettings', this);
      }
    }

    Setup = ExtensibleSetup;
  }

  if(typeof Game !== 'undefined') {
    const _Game = Game;

    class ExtensibleGame extends _Game {
      registerSettings() {
        super.registerSettings();
        Hooks.call('post.game.registerSettings', this);
      }
    }

    Game = ExtensibleGame;
  }

  console.log(`ExtensibleAuthPlugin | Loaded`);
});

