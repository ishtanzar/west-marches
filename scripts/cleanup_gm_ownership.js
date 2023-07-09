await (async () => {
    const apiToken = 'suq3omH.hB_QyTuV61_6';
    const discordToken = 'ODUxNDgxNDkzNTM1NDU3MzMx.YL457w.lJtFEeZjQaKd86JhJCq0_jf_ROk';

    const apiRes = await fetch('https://api.westmarchesdelacave.ishtanzar.net/users', {headers: {Authorization: 'ApiKey-v1 ' + apiToken}});
    const discordRes = await fetch('https://discord.com/api/guilds/776895471875915837/members?limit=50', {
        headers: {
            Authorization: 'Bot ' + discordToken
        }
    });

    const discordGMs = (await discordRes.json()).reduce((users, u) => {
        if((u.user.bot || false) === false) {
            users.push(u.user.id);
        }
        return users;
    }, [])

    const foundryGMs = (await apiRes.json()).reduce((users, u) => {
        if (discordGMs.includes(u.value.discord.id)) {
            users.push(u.value.foundry._id)
        }
        return users;
    }, []);

    const actors = await new Promise(resolve => {
        db.Actor.db.find().exec((err, docs) => resolve(docs))
    });

    for (const a of actors) {
        let folder, folderId = a.folder;
        do {
            [folder] = await db.Folder.find({_id: folderId});
            folderId = folder.data.parent
        } while (folderId);

        let newPerms = {default: a.permission.default};

        if(['vqQyLrFzMbWIQyK3', 'CIlYFrkfmjt42rWA'].includes(folder.id)) {
            const ownerIds = Object.keys(a.permission);
            if(ownerIds.length > 2) {
                for(const ownerId of ownerIds) {
                    if(!foundryGMs.includes(ownerId)) {
                        newPerms[ownerId] = a.permission[ownerId]
                    }
                }
            }
            console.log(`${a.name} (${a._id}): ${(await Promise.all(Object.keys(newPerms).map(async i => (await db.User.get(i))?.name))).join(', ')}`)
        } else {
            console.log(`${a.name} (${a._id}) is NPC`);
        }

        a.permission = newPerms;

        await new Promise(resolve => {
            db.Actor.db.update({_id: a._id}, a, {}, (err, count) => resolve(count))
        });
    }
})();