import ExtensibleAuthFoundryPlugin from "./main.mjs";
import JoinView from 'foundry:dist/server/views/join.mjs';
import GameView from 'foundry:dist/server/views/game.mjs';

describe('ExtensibleAuth Plugin', () => {
    it('should have access_key method by default', async () => {
        const extensiblePluginBase = {
            addStaticFilesDirectory: jasmine.createSpy(),
                hooks: jasmine.createSpyObj('base', ['on', 'callAsync'])
        };

        const plugin = new ExtensibleAuthFoundryPlugin(extensiblePluginBase);
        plugin.staticFiles();

        expect(extensiblePluginBase.addStaticFilesDirectory).toHaveBeenCalledOnceWith(
            jasmine.stringMatching(`${plugin.constructor.MODULE_NAME}/public`),
            jasmine.stringMatching(plugin.constructor.MODULE_NAME)
        );

        const callback = jasmine.createSpy('resolve callback');
        await plugin.getLoginData(callback)

        expect(callback).toHaveBeenCalledOnceWith({methods: ['access_key']});
    });

});

describe('Foundry login page', () => {
    it('should render with extensibleAuth scripts', async () => {
        const callSpy = spyOn(extensibleFoundry.hooks, 'call').and.callThrough();
        const staticContent = JoinView._getStaticContent({setup: true});

        expect(callSpy).toHaveBeenCalledWith('post.views.join.getStaticContent', jasmine.any(Object));
        expect(staticContent.scripts.map(s => s.src)).toContain('modules/extensibleAuth/scripts/join.js');
    })
})

describe('Foundry game page', () => {
    it('should render with extensibleAuth scripts', async () => {
        const moduleConfig = await global.db.Setting.getValue("core.moduleConfiguration") || {};
        const staticContent = GameView._getStaticContent({world: true, moduleConfig: moduleConfig});
        expect(staticContent.scripts.map(s => s.src)).toContain('/modules/extensibleAuth/modules/main.mjs');
    })
})