## Foundry Extensible Plugin

### What's that about

This extensible plugin aims at providing Foundry community a way to extend on the server side.
Foundry has an awesome way of plugins to support many RPG systems, various modules, etc; but when it comes to server-side changes like authentication mecanisms, static pages, integrations, there's no documented API nor easy ways to do it.

### Usage

This plugin leverages node's --require option to run at startup and the override-require package to override Foundry classes with hooks.
The base plugin comes with a set of basic plugins as examples (api, metrics, extensibleOAuth).

Also, you need to install some NPM packages that or required for either the base plugin or the additional plugins.
The easiest way to handle this is to use a Docker image

### Plugin development

Suggested plugin structure:

```
my-plugin
├── main.js
└── templates
    └── views
        └── my-view.hbs
```

Some examples:

```javascript
'use strict';

class MyPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    // Add a new route
    base.hooks.on('pre.express.defineRoutes', router => router.get('/my-route', this.get));
    
    // Add the templates/views folder to the list of views so you can override an existing view
    base.hooks.once('post.express.createApp', app => {
      app.set('views', [path.join(__dirname, 'templates', 'views')].concat(app.get('views')));
    });
    
    // Extend User entity with new fields
    base.hooks.once('post.user.schema', schema => {
      schema['my-field'] = {
        'type': Object,
        'required': !![],
        'default': {},
        'validate': () => true,
        'validationError': 'Invalid object structure'
      }

    });
  }
  
  async get(req, res) {
    resp.render('my-view', {
      'myVariable': 'some value'
    });
  }
}

module.exports = MyPlugin;
```
