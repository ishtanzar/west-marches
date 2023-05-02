import morgan from "morgan";

export default class AccessLogsPlugin {

    /**
     *
     * @param {ExtensibleFoundryPlugin} base
     */
    constructor(base) {
        const stream = {
            write: (message) => global.logger.http(message)
        };

        base.hooks.on('pre.express.middleware', router => {
            router.use(morgan(
                ':remote-addr ":method :url HTTP/:http-version" :status :res[content-length] ":referrer" ":user-agent"',
                {stream: stream }
            ));
        });
    }
}