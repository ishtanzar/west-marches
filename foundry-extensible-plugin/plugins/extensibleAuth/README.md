## Foundry Extensible Plugin - Extensible Auth Module

At the time of this writing, only Access Key auth is available.
The concept I understand in it so far is really that *the* GM sets up the keys of each players, period.

Now, it can be useful for public servers to offer alternate authentication mecanisms like Oauth (Discord, Facebook, Google, whatever).
The goal of this public is to offer the foundation for people to write additional auth modules.

You can also disable Access Key authentication when you have everything correctly set up.

There are currently 2 known additional auth modules:
* JWT
* Discord OAuth

### JWT - extensibleAuthJwt

This is really just a support plugin. On successful login, an access_token cookie is sent and contains the userId.

The home view is replaced and verify any existing JWT, reads the userId and redirect to /game if everything worked fine.
Otherwise, redirect to the regular /join view.

### Discord - extensibleAuthDiscord

Implements Discord Auth mechanism. Once enabled, you need to configure the OAuth settings from the "Modules Config" window within Foundry.

### How to write your own auth module

#### Minimal module structure

```
myAuthModule
├── main.js
└── templates/views/partials/my_auth.hbs
```

main.js
```javascript
'use strict';

class MyAuthPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    base.hooks.on('extensibleAuth.route_join.auths', this.configure);
    base.hooks.on('extensibleAuth.route_settings.settings', this.get_settings);

    // Declare your templates/views/partials directory, this is required in order to contribute to the /join view
    base.hooks.on('pre.express-handlebars.config', config => {
      config.partialsDir = (config.partialsDir || []).concat([path.join(__dirname, 'templates', 'views', 'partials')])
    });
  }

  /**
   * Add anything you need on the /join view for your plugin (at least if this auth is enabled)
   */
  async configure(auths) {
    auths['my_auth'] = {
      enabled: true
    }
  }

  /**
   * Use this to declare any setting you want to display in the "Module Settings" window
   * The foundry-extensible-auth-module in extensibleAuth is a regular Foundry module pushed by to backend and 
   * automatically enabled to declare the settings.
   * 
   * Check foundry-extensible-plugin/plugins/extensibleAuth/foundry-extensible-auth-module for more details
   */
  async get_settings(settings) {
    [
      {
        module: 'foundry-extensible-auth-module',
        key: 'my_auth.enabled',
        name: 'MyAuth.Enabled.Name',
        scope: 'world',
        config: true,
        type: 'Boolean', // Beware of using a String that will be converted by the frontend module in a proper type class
        default: false
      },
    ].map(setting => {settings.push(setting)});
  }
}
```

templates/views/partials/my_auth.hbs
```handlebars
{{#if enabled}}
    <p>My Authentication plugin works, just need to add some logic !</p>
{{/if}}
```

Now, until the plugin install is made easy or at least dynamic, you need to add your plugin in
foundry-extensible-plugin/override/dist/init.js:

```javascript
    // TODO: dynamic plugin list
    for(let plugin of ['api', 'metrics', 'extensibleAuth', 'extensibleAuthDiscord', 'extensibleAuthJwt', 'myAuthModule']) {
      const cls = require(path.join(pluginsPath, plugin, 'main'));
      this._plugins.push(new cls(this._instance));
    }
```