import View from 'foundry:dist/server/views/view.mjs';

export default class ExtensibleView extends View {

    static _getStaticContent({world: e = !1, setup: s = !1, moduleConfig: t = {}}) {
        return View._getStaticContent({world: e, setup: s, moduleConfig: t});
    }
}