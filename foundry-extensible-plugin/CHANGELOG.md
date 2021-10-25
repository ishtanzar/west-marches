# [1.3.0](https://github.com/ishtanzar/west-marches/compare/releases/foundry-extensible-plugin/v1.2.1...releases/foundry-extensible-plugin/v1.3.0) (2021-09-29)


### Features

* **socket:** add pre.sockets.activate hook to add custom socket event handlers ([2b8fd1a](https://github.com/ishtanzar/west-marches/commit/2b8fd1a57fab4273849617622faa5de392b4316b))
* **westmarches:** add discordSend & createOrUpdateGameSession socket event handlers ([f0618d9](https://github.com/ishtanzar/west-marches/commit/f0618d965c1637870c7303db0905f48a968d6623))



## [1.2.1](https://github.com/ishtanzar/west-marches/compare/releases/foundry-extensible-plugin/v1.2.0...releases/foundry-extensible-plugin/v1.2.1) (2021-09-17)


### Bug Fixes

* **kanka:** Uncaught TypeError game.users.current.data.auth.kanka is undefined ([069b723](https://github.com/ishtanzar/west-marches/commit/069b723d10c9911cf72a15f36c768acf2cb370fa))



# [1.2.0](https://github.com/ishtanzar/west-marches/compare/releases/foundry-extensible-plugin/v1.1.0...releases/foundry-extensible-plugin/v1.2.0) (2021-09-14)


### Features

* **kanka:** improve login chat message with translations ([8cd7c94](https://github.com/ishtanzar/west-marches/commit/8cd7c9426f5dd417ce4bcd427d9629b54c6153e9))
* **kanka:** login on kanka via OAuth ([11dfe69](https://github.com/ishtanzar/west-marches/commit/11dfe693ab7b37cd4cdf867e9f4e4438d1f45e23))
* **overrides:** override User.getUsers so the custom schema is sent to the UI ([96e1d50](https://github.com/ishtanzar/west-marches/commit/96e1d50b20d538955694218d50191ea64c61797c))



# [1.1.0](https://github.com/ishtanzar/west-marches/compare/releases/foundry-extensible-plugin/v1.0.1...releases/foundry-extensible-plugin/v1.1.0) (2021-09-12)


### Bug Fixes

* **api:** fix 404 on PUT /api/users/<userId> ([aa9be5a](https://github.com/ishtanzar/west-marches/commit/aa9be5a884f800c760bfe758c1a9e7a8714804cd))


### Features

* **api:** add GET /api/users ([99e12f1](https://github.com/ishtanzar/west-marches/commit/99e12f1940dc6421a17172c862ac7bfa1af61a39))
* **discord-auth:** remove discord email on API get ([07b2739](https://github.com/ishtanzar/west-marches/commit/07b2739c0d2d6fd5824f7290a4caa06fb4c77caa))
* **discord-auth:** store some discord data on user creation ([10b23fb](https://github.com/ishtanzar/west-marches/commit/10b23fb087d3753fe3b248092049bedd9a7e3547))



## [1.0.1](https://github.com/ishtanzar/west-marches/compare/releases/foundry-extensible-plugin/v1.0.0...releases/foundry-extensible-plugin/v1.0.1) (2021-09-11)


### Bug Fixes

* **discord-auth:** redirect_uri is empty, timeout on invalid user, discord details not stored on user document, removed duplicated join.hbs JS ([cc0ef56](https://github.com/ishtanzar/west-marches/commit/cc0ef56632c44c4c2d05ef6717c66b3b498f25d4))



# [1.0.0](https://github.com/ishtanzar/west-marches/compare/bd82b817f9c8b0b3f531428b6dd8a5acf1073a11...releases/foundry-extensible-plugin/v1.0.0) (2021-09-08)


### Code Refactoring

* **server-module:** major refactoring and rename as extensible-plugin + plugins ([bd82b81](https://github.com/ishtanzar/west-marches/commit/bd82b817f9c8b0b3f531428b6dd8a5acf1073a11))


### Features

* **extensible-plugin:** add extensibleAuth module & discord auth refactoring ([b54453d](https://github.com/ishtanzar/west-marches/commit/b54453d9c251e60449958c8cfc5b1816da1262b4))
* **extensible-plugin:** each auth mecanism can contribute to the join view with partials ([509a9a9](https://github.com/ishtanzar/west-marches/commit/509a9a962352b47a3360031c0a81f273db00d2b0))
* **extensible-plugin:** improve discord login experience ([7c17278](https://github.com/ishtanzar/west-marches/commit/7c17278eea8ba564e60977ba545f17383d4d1a94))
* **extensible-plugin:** overrides reorg + extensibleAuthJwt plugin ([a02b333](https://github.com/ishtanzar/west-marches/commit/a02b33365f3d8cb02d2f2cc38f0fb9bf11b25443))


### BREAKING CHANGES

* **server-module:** The wm-backend-plugin is now known as foundry-extensible-plugin and existing features are moved as plugins.



