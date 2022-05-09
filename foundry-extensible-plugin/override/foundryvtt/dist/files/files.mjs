import BaseFiles from "foundry:dist/files/files.mjs";

export default class Files extends BaseFiles {

  static loadTemplate(e) {
    const template = BaseFiles.loadTemplate(e);
    extensibleFoundry.hooks.call('post.files.loadTemplate', e, template);

    return template;
  }

}