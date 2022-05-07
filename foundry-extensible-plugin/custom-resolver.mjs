
import winston from "winston";
import path from "path";
import fs from "fs";

const logger = (global.extensibleLogger || winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp({format: "YYYY-MM-DD HH:mm:ss"}),
    winston.format.errors({stack: true}),
    winston.format.json()
  ),
  transports: new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.printf((o => {
        let line = `ExtensiblePlugin | ${o.timestamp} | [${o.level}] ${o.message}`;
        return o.stack && (line += "\n" + o.stack), line
      }))
    )
  })
}));

global.extensibleLogger = logger;

export function resolve(specifier, context, defaultResolve) {
  const { parentURL = null } = context;
  logger.debug(`Resolving ${specifier} from ${parentURL}`);
  const pluginRoot = new URL('./', import.meta.url);

  if(specifier.startsWith('foundry:') && global.foundryRoot) {
    specifier = path.resolve(global.foundryRoot, specifier.split(':')[1]);
  }

  if(parentURL) {
    const requested = new URL(specifier, parentURL);
    const relative = path.relative((global.foundryRoot?new URL('file://'+foundryRoot):new URL('./', parentURL)).pathname, requested.pathname);

    if(relative) {
      const override = new URL(relative, new URL('./override/', pluginRoot))

      if(fs.existsSync(override.pathname) && override.href !== parentURL) {
        logger.info(`Found an override for ${specifier} as ${override.href}`);
        return {
          url: override.href
        }
      }
    }
  }

  return defaultResolve(specifier, context, defaultResolve);
}