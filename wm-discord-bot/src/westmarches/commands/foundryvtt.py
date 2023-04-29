import datetime
import logging
import os
import random
import string
from abc import abstractmethod
from discord import Embed, Member
from discord.ext.commands import Context
from operator import itemgetter
from redbot.core import commands, checks
from typing import Optional

from westmarches.utils import CompositeMetaClass, MixinMeta

log = logging.getLogger("red.westmarches.foundry")


class FoundryCommands(MixinMeta, metaclass=CompositeMetaClass):

    @abstractmethod
    async def discord_api_wrapper(self, ctx: Context, messages_key: str, f):
        pass

    def __init__(self) -> None:
        super().__init__()

    @property
    def foundry_url(self):
        return 'http://%s:5000' % os.environ['FOUNDRY_HOST']

    @property
    def foundry_auth(self):
        return 'foundry_manager', os.environ['MANAGER_API_SECRET']

    async def fetch_foundry_user_from_discord(self, discord_user: Optional[Member]):
        foundry_users = await self.api_client.foundry.users({'discord.id': discord_user.id})
        foundry_user = next(iter(foundry_users['users']), None)

        return foundry_user if foundry_user else None

    @checks.has_permissions(administrator=True)
    @commands.group(name="foundry")
    async def command_foundry(self, ctx: commands.Context):
        """Foundry admin commands"""

    @command_foundry.command(name="heroes")
    async def heroes_list(self, ctx: commands.Context):
        resp = await self.api_client.foundry.actors()
        grouped_roster = {}

        for actor in resp['actors']:
            pc_race = actor['data']['details']['race']
            pc_classes = [(c['name'], c['data']['levels']) for c in actor['items'] if 'class' == c['type']]

            pc = {
                'name': actor['name'],
                'race': pc_race.split(maxsplit=1)[0] if pc_race else '',
                'class': max(pc_classes, key=itemgetter(1))[0] if pc_classes else '',
            }

            if pc['class']:
                if pc['class'] not in grouped_roster:
                    grouped_roster[pc['class']] = []

                grouped_roster[pc['class']].append(pc)

        async with self.config.messages() as messages:
            await ctx.send(messages['foundry.roster.intro'] % self.bot.user.display_name.split(maxsplit=1)[0])

        await ctx.send(embed=Embed(
            description="\n".join(['• %s : %s' % (c, ', '.join([pc['name'] for pc in grouped_roster[c]])) for c in grouped_roster])
        ))

    @command_foundry.command(name="heroes_class")
    async def heroes_class_search(self, ctx: commands.Context, pc_class: str):
        resp = await self.api_client.foundry.actors()
        heroes = []

        for actor in resp['actors']:
            pc_classes = [c['name'].lower() for c in actor['items'] if 'class' == c['type']]
            if pc_class.lower() in pc_classes:
                heroes.append(actor['name'])

        async with self.config.messages() as messages:
            await ctx.send(messages['foundry.roster.search.class'] % (pc_class, ', '.join(heroes)))

    @command_foundry.command()
    async def player_add(self, ctx: commands.Context, user: Member):
        """Add a new user to Foundry from Discord"""
        await self.api_client.foundry.users_add(user.name, discord={
            "id": str(user.id),
            "username": user.name,
            "avatar": user.avatar,
            "discriminator": str(user.discriminator),
        })

        async with self.config.messages() as messages:
            await ctx.send(messages['foundry.player.add.done'] % user.name)

    @command_foundry.command()
    async def player_link(self, ctx: commands.Context, foundry_username: Optional[str], user: Optional[Member]):
        """Link a Discord user with a Foundry user"""
        if not user:
            user = ctx.message.author

        foundry_users = await self.api_client.foundry.users(
            {'name': foundry_username if foundry_username else user.name})

        foundry_user = next(iter(foundry_users['users']), None)

        async with self.config.messages() as messages:
            if foundry_user:
                await self.api_client.foundry.users_update(foundry_user['_id'], discord={
                    "id": str(user.id),
                    "username": user.name,
                    "avatar": user.avatar,
                    "discriminator": str(user.discriminator),
                })
                await ctx.message.add_reaction('\U00002705')  # :white_check_mark:
            else:
                await ctx.send(messages['foundry.player.discord.not_found'] % user.name)

    @command_foundry.command()
    async def player_set_gm(self, ctx: commands.Context, discord_user: Optional[Member]):
        """Switch a Foundry user as GM (need the Discord user to be linked with a Foundry user either by login or
        by using the link command)"""
        if not discord_user:
            discord_user = ctx.message.author

        foundry_user = await self.fetch_foundry_user_from_discord(discord_user)
        async with self.config.messages() as messages:
            if foundry_user:
                await self.api_client.foundry.users_update(foundry_user['_id'], role=4)
                await ctx.send(messages['foundry.player.toggle_gm.activate'] % discord_user.name)
            else:
                await ctx.send(messages['foundry.player.discord.not_found'] % discord_user.name)

    @command_foundry.command()
    async def player_remove_gm(self, ctx: commands.Context, discord_user: Optional[Member]):
        """Switch a Foundry user as Player (need the Discord user to be linked with a Foundry user either by login or
        by using the link command)"""
        if not discord_user:
            discord_user = ctx.message.author

        foundry_user = await self.fetch_foundry_user_from_discord(discord_user)
        async with self.config.messages() as messages:
            if foundry_user:
                await self.api_client.foundry.users_update(foundry_user['_id'], role=1)
                await ctx.send(messages['foundry.player.toggle_gm.deactivate'] % discord_user.name)
            else:
                await ctx.send(messages['foundry.player.discord.not_found'] % discord_user.name)

    @command_foundry.command(name="reset_password")
    async def player_reset_password(self, ctx: commands.Context, discord_user: Member):
        """Update a Foundry user with a random password and send it to you via PM"""
        foundry_user = await self.fetch_foundry_user_from_discord(discord_user)
        async with self.config.messages() as messages:
            if foundry_user:
                new_password = ''.join(
                    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(12))
                await self.api_client.foundry.users_update(foundry_user['_id'], password=new_password)
                await discord_user.send(messages['foundry.player.password.reset'] % new_password)
                await ctx.message.add_reaction('\U00002705')  # :white_check_mark:
            else:
                await ctx.send(messages['foundry.player.discord.not_found'] % discord_user.name)

    @command_foundry.command(name="online")
    async def activity_users(self, ctx: commands.Context):
        """List users connected to Foundry"""
        async with self.config.messages() as messages:
            users = await self.api_client.foundry.activity()
            if users['users']:
                await ctx.send(messages['foundry.activity.users'] % ', '.join(users['users']))
            else:
                await ctx.send(messages['foundry.activity.no_users'])

    @command_foundry.command(name="restart")
    async def command_restart(self, ctx: commands.Context):
        """Restart FoundryVTT"""
        await self.discord_api_wrapper(ctx, 'foundry.restart', lambda: self.api_client.foundry.restart())

    @command_foundry.group(name="backup", invoke_without_command=True)
    async def foundry_backup(self, ctx: commands.Context):
        """Perform a backup of FoundryVTT. Beware that Foundry WILL BE STOPPED"""

        await self.discord_api_wrapper(ctx, 'foundry.backup', lambda: self.api_client.foundry.backup())

    @foundry_backup.command(name="list")
    async def foundry_backup_list(self, ctx: commands.Context):
        """List existing backups"""
        response = await self.api_client.foundry.list_backups()

        backup: dict
        for backup in response['backups']:
            await ctx.send('`%s - %s - %s`' % (
                backup['_id'],
                backup['schema'],
                datetime.datetime.strptime(backup['date'], '%Y-%m-%d-%H-%M-%f').strftime('%d/%m/%Y %H:%M')
            ))

    @foundry_backup.command(name="restore")
    async def foundry_backup_restore(self, ctx: commands.Context, backup_id: str):
        """Restore a backup"""
        await self.discord_api_wrapper(
            ctx, 'foundry.backup_restore', lambda: self.api_client.foundry.restore(backup_id)
        )
