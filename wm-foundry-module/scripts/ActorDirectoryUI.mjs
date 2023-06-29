
export default class ActorDirectoryUI {

    static initialize() {
        let {CONFIG, Hooks} = window;

        Hooks.on('init', () => { CONFIG.debug.hooks = true });
        Hooks.on('setup', () => { CONFIG.debug.hooks = true });
        Hooks.on('ready', () => { CONFIG.debug.hooks = true });

        Hooks.on('getActorDirectoryEntryContext', ($html, options) => {
            options.push({
                name: 'Claim actor',
                icon: '<i class="fas fa-lock fa-fw"></i>',
                condition: li => {
                    return game.user.isGM && !ActorDirectoryUI.isActorOwnerFromDirectoryEntry(li, window.game.user);
                },
                callback: li => {
                    ActorDirectoryUI.onToggleClaimActor(ActorDirectoryUI.getActorFromDirectoryEntry(li), window.game.user, true);
                }
            }, {
                name: 'Unclaim actor',
                icon: '<i class="fas fa-unlock fa-fw"></i>',
                condition: li => {
                    return game.user.isGM && ActorDirectoryUI.isActorOwnerFromDirectoryEntry(li, window.game.user);
                },
                callback: li => {
                    ActorDirectoryUI.onToggleClaimActor(ActorDirectoryUI.getActorFromDirectoryEntry(li), window.game.user, false);
                }
            });
            return options;
        })

        Hooks.on('getActorDirectoryFolderContext', ($html, options) => {
            options.push({
                name: 'Recursively claim actors',
                icon: '<i class="fas fa-lock fa-fw"></i>',
                condition: () => {
                    return game.user.isGM;
                },
                callback: li => {
                    ActorDirectoryUI.onRecursiveToggleClaim(li, true);
                }
            },{
                name: 'Recursively unclaim actors',
                icon: '<i class="fas fa-unlock fa-fw"></i>',
                condition: () => {
                    return game.user.isGM;
                },
                callback: li => {
                    ActorDirectoryUI.onRecursiveToggleClaim(li, false);
                }
            });
            return options;
        })
    }

    static onRecursiveToggleClaim(li, claim = true) {
        const actors = ActorDirectoryUI.recursiveListActors(ActorDirectoryUI.getFolderFromDirectoryEntry(li));

        for(const actor of actors) {
            ActorDirectoryUI.onToggleClaimActor(actor, window.game.user, claim);
        }

    }

    static recursiveListActors(folder) {
        const actors = folder.content;

        for(child of folder.children) {
            actors.concat(this.recursiveListActors(child));
        }

        return actors;
    }

    static isActorOwnerFromDirectoryEntry(li, user) {
        return ActorDirectoryUI.getActorFromDirectoryEntry(li).testUserPermission(user, "OWNER", {exact: true});
    }

    static getFolderFromDirectoryEntry(li) {
        return game.folders.get(li.parent().data('folderId'))
    }

    static getActorFromDirectoryEntry(li) {
        let {game} = window;
        let [major, _] = (game.version || "").split(".");

        const entity = ActorDirectory.collection.get(li.data(major >= 9 ? "documentId" : "entityId"));
        return game.actors.get(entity.id);
    }

    static onToggleClaimActor(actor, user, claim = true) {
        let perms = actor.data.permission;

        if(claim) {
            perms[user.id] = 3;
        } else {
            delete perms[user.id];
        }

        actor.update({permission: perms}, {diff: false, recursive: false, noHook: true});
    }

}