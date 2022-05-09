import {UserData as BaseUserData} from "foundry:common/data/data.mjs";

export class UserData extends BaseUserData {
  static defineSchema() {
    const {extensibleFoundry} = global;

    const schema = BaseUserData.defineSchema();
    extensibleFoundry.hooks.call('post.user.defineSchema', schema);

    return schema;
  }
}

export * from "foundry:common/data/data.mjs";