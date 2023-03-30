import winston from "winston";
import path from "path";
import fs from "fs";
import url from "url";

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
global.extensiblePluginRoot = path.dirname(url.fileURLToPath(import.meta.url));

export async function resolve(specifier, context, defaultResolve) {
  const { parentURL = null } = context;
  logger.debug(`Resolving ${specifier} from ${parentURL}`);
  const pluginRoot = path.dirname(new URL(import.meta.url).pathname);

  if(specifier.startsWith('foundry:') && global.foundryRoot) {
    specifier = path.resolve(global.foundryRoot, specifier.split(':')[1]);
  }

  if(parentURL) {
    if(!global.foundryRoot) {
      const currentPath = path.dirname(new URL(parentURL).pathname), pkgFile = path.join(currentPath, 'package.json');
      if(fs.existsSync(pkgFile)) {
        const pkgContent = JSON.parse(fs.readFileSync(pkgFile, {encoding: "utf8"}));
        if(pkgContent.name === 'foundryvtt') {
          global.foundryRoot = currentPath;
        }
      }
    }

    let requested, override;
    if(specifier.startsWith('.') || specifier.startsWith('/') || specifier.startsWith('file://')) {
      requested = new URL(specifier, parentURL);
      override = new URL(requested.href.replace(global.foundryRoot, path.join(pluginRoot, 'override', 'foundryvtt')));
    } else {
      const nextResult = await defaultResolve(specifier, context);
      requested = nextResult.url;
      if(requested.startsWith('node:')) {
        return nextResult;
      } else {
        override = new URL(requested.replace(path.join(global.foundryRoot, 'node_modules'), path.join(pluginRoot, 'override')));
      }
    }

    if(fs.existsSync(override.pathname) && override.href !== parentURL && override.href !== requested.href) {
      logger.info(`Found an override for ${specifier} as ${override.pathname}`);

      return {
        url: override.href
      }
    }
  }

  return defaultResolve(specifier, context, defaultResolve);
}
