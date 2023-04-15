import JoinView from 'foundry:dist/server/views/join.mjs';
import sessions from "foundry:dist/sessions.mjs";

class StaticCallJoinView extends JoinView {

    async handleGet(s, e) {
        const {game: t} = global;
        if (!t.world) return this._noWorld(s, e);
        if (!t.ready) return setTimeout((() => this.handleGet(s, e)), 1e3);
        sessions.logoutWorld(s, e);
        const o = t.world ? t.world.background : null, a = this.constructor._getStaticContent({setup: !0});
        return e.render(this._template, {
            bodyClass: "vtt players " + (o ? "background" : ""),
            bodyStyle: `background-image: url('${o || "ui/denim075.png"}')`,
            messages: sessions.getMessages(s),
            scripts: a.scripts,
            styles: a.styles
        })
    }

}

export default class ExtensibleJoinView extends StaticCallJoinView {

    async handleGet(s, e) {
        const opts = {
            view: this,
            req: s,
            resp: e
        }

        await extensibleFoundry.hooks.callAsync('pre.views.join.handleGet', opts);
        return await super.handleGet(opts.req, opts.resp);
    }

    static _getStaticContent({world: world = false, setup: setup = false, moduleConfig: moduleConfig = {}}) {
        const result = super._getStaticContent({world: world, setup: setup, moduleConfig: moduleConfig});

        extensibleFoundry.hooks.call('post.views.join.getStaticContent', {
            params: {world: world, setup: setup, moduleConfig: moduleConfig},
            result: result
        });

        return result;
    }
}