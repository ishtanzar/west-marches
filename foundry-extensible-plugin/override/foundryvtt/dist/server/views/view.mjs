import View from 'foundry:dist/server/views/view.mjs';

export default class ExtensibleView extends View {

    static _getStaticContent({world: e = !1, setup: s = !1, moduleConfig: t = {}}) {
        return View._getStaticContent({world: e, setup: s, moduleConfig: t});
    }

    static home(req, res) {
        let result;

        if(!(extensibleFoundry.hooks.call('pre.views.home', {req: req, res: res}) === false)) {
            result = super.home(req, res);
        }

        extensibleFoundry.hooks.call('post.views.home', {
            params: {req: req, res: res},
            result: result
        });

        return result;
    }
}