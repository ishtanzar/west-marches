'use strict';

const {paths} = global;
const {Views} = require(paths.code + '/views');


class ExtensibleViews extends Views {

  static async home(req, resp) {
    const {extensibleFoundry} = global;
    const params = {
      req: req,
      resp: resp,
      replace: false
    }

    await extensibleFoundry.hooks.callAsync('pre.views.home', params);

    if(!params.replace) {
      params.result = await Views.home(params.req, params.resp);
    }

    await extensibleFoundry.hooks.callAsync('post.views.home', params);

    return params.result;
  }

}

module.exports = {'Views': ExtensibleViews};
