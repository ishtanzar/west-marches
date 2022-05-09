import fs from "fs";
import path from "path";
import url from "url";
import express from "express";

export default class ExtensibleAuthFoundryPlugin {

  /**
   *
   * @param {ExtensibleFoundryPlugin} base
   */
  constructor(base) {
    base.hooks.on('post.files.loadTemplate', this.loadTemplate);
    base.hooks.on('post.express.staticFiles', this.staticFiles);
    base.hooks.on('post.express.CORE_VIEW_SCRIPTS', this.viewScripts);
  }

  loadTemplate(relative, template) {
    const templatesRoot = path.dirname(url.fileURLToPath(import.meta.url));
    const absolute = path.join(templatesRoot, relative);

    if(fs.existsSync(absolute)) {
      Object.assign(template, delete template['error'], {
        html: fs.readFileSync(absolute, {encoding: "utf8"}),
        success: true
      });
    }
  }

  staticFiles(app) {
    app.use(express.static(path.join(path.dirname(url.fileURLToPath(import.meta.url)), 'public')));
  }

  viewScripts(modules) {
    modules.push('scripts/extensibleAuth.js');
  }
}
