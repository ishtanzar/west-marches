'use strict';

const {paths} = global;
const {Views} = require(paths.code + '/views');


class ExtensibleViews extends Views {

  static home(req, resp) {
    const {game} = global;
    if (config.license.needsSignature) return resp.redirect(req.baseUrl + '/license');

    if (game.world) {
      if (!req.user) {
        const bgClass = game.world ? game.world.background : null;

        return resp.render('home', {
          'bodyClass': "vtt players " + (bgClass ? "background" : ''),
          'bodyStyle': 'background-image:\x20url(\x27' + (bgClass || "ui/denim075.png") + '\x27)',
        });
      }
      return resp.redirect(req.baseUrl + '/game');
    }
    return resp.redirect(req.baseUrl + '/setup');
  }

}

module.exports = {'Views': ExtensibleViews};
