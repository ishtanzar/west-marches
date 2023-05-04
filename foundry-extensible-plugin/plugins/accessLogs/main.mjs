import morgan from "morgan";

export default class AccessLogsPlugin {

    /**
     *
     * @param {ExtensibleFoundryPlugin} base
     */
    constructor(base) {
        const stream = {
            write: (message) => {
                //remove last \n from message: https://github.com/expressjs/morgan/blob/1.10.0/index.js#L130
                const index = message.lastIndexOf("\n");
                if(index > 0) {
                    message = message.substring(0, index) + message.substring(index + 1)
                }

                global.logger.http(message)
            }
        };

        morgan.token('req-headers', (req, res) => JSON.stringify(req.headers))
        morgan.token('req-body', (req, res) => JSON.stringify(req.body))

        base.hooks.on('pre.express.middleware', router => {
            router.use(morgan(
                ':remote-addr ":method :url HTTP/:http-version" :status :res[content-length] ":referrer" ":user-agent"',
                {stream: stream }
            ));

            router.use('/api/users/*', morgan(
                'req.headers=:req-headers, req.body=:req-body, resp.body=:res[body]',
                {stream: stream }
            ))
        });
    }
}