import Setting from 'foundry:dist/database/documents/setting.mjs';

export default class ExtensibleSetting extends Setting {

  async save() {
    await extensibleFoundry.hooks.callAsync('pre.setting.save', this);
    return await super.save();
  }

}