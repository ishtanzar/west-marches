import World from 'foundry:dist/packages/world.mjs';

export default class ExtensibleWorld extends World {

  get modules() {
    const modules = super.modules;
    extensibleFoundry.hooks.call('post.world.modules', modules);
    return modules;
  }

}

