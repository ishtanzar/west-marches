import Jasmine from "jasmine";

export default class ServerTestPlugin {

    /**
     *
     * @param {ExtensibleFoundryPlugin} base
     */
    constructor(base) {
        base.hooks.on('post.initialize', this.initialize);
    }

    async initialize() {
        const {extensibleLogger, logger} = global;
        logger.info('Running tests');

        // const projectRoot = '/home/foundry/resources/foundry-extensible-plugin';

        // const result = await jest.runCLI({
        //     json: false,
        //     passWithNoTests: true,
        //     testEnvironment: 'node',
        //     testMatch: ['**/*.spec.mjs'],
        //     transform: {}
        // }, [projectRoot]);

        const jasmine = new Jasmine();
        jasmine.loadConfig({
            spec_dir: '.',
            spec_files: [
                '**/*.spec.mjs'
            ]
        });
        jasmine.exitOnCompletion = false;

        const result = await jasmine.execute();
    }
}