import logging
import os
from abc import abstractmethod
from discord import Member
from discord.ext.commands import Context
from redbot.core import commands, checks
from typing import Optional
from westmarches_utils.queue import Queue, JobDefinition
from westmarches_utils.config import Config

from westmarches.utils import CompositeMetaClass, MixinMeta
from westmarches_utils.api import HTTPException

log = logging.getLogger("red.westmarches.foundry")


class FoundryCommands(MixinMeta, metaclass=CompositeMetaClass):

    @abstractmethod
    async def discord_api_wrapper(self, ctx: Context, messages_key: str, f):
        pass

    @property
    def foundry_url(self):
        return 'http://%s:5000' % os.environ['FOUNDRY_HOST']

    @property
    def foundry_auth(self):
        return 'foundry_manager', os.environ['MANAGER_API_SECRET']

    @checks.has_permissions(administrator=True)
    @commands.group(name="foundry")
    async def command_foundry(self, ctx: commands.Context):
        """Foundry admin commands"""

    @command_foundry.command()
    async def player_add(self, ctx: commands.Context, user: Member):
        """Add a new user to Foundry from Discord"""
        await self.wm_api.management.foundry.users_add(user.name, discord={
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

        foundry_users = await self.wm_api.management.foundry.users(
            {'name': foundry_username if foundry_username else user.name})

        foundry_user = next(iter(foundry_users['users']), None)

        async with self.config.messages() as messages:
            if foundry_user:
                await self.wm_api.management.foundry.users_update(foundry_user['_id'], discord={
                    "id": str(user.id),
                    "username": user.name,
                    "avatar": user.avatar,
                    "discriminator": str(user.discriminator),
                })
                await ctx.message.add_reaction('\U00002705')  # :white_check_mark:
            else:
                await ctx.send(messages['foundry.player.discord.not_found'] % user.name)

    async def update_role(self, ctx: commands.Context, discord_user: Optional[Member], role: int):
        if not discord_user:
            discord_user = ctx.message.author

        try:
            api_user = await self.wm_api.users.findOne({'discord.id': str(discord_user.id)})

            if api_user:
                await self.wm_api.management.foundry.users_update(api_user['value']['foundry']['_id'], role=role)
                await self.wm_api.users.update(api_user['key'], {'foundry': {'role': role}})

                await ctx.message.add_reaction('\U00002705')
        except HTTPException as e:
            await ctx.send(str(e.asdict()))

    @command_foundry.command()
    async def player_set_gm(self, ctx: commands.Context, discord_user: Optional[Member]):
        """Switch a Foundry user as GM (need the Discord user to be linked with a Foundry user either by login or
        by using the link command)"""
        await self.update_role(ctx, discord_user, 4)

    @command_foundry.command()
    async def player_remove_gm(self, ctx: commands.Context, discord_user: Optional[Member]):
        """Switch a Foundry user as Player (need the Discord user to be linked with a Foundry user either by login or
        by using the link command)"""
        await self.update_role(ctx, discord_user, 1)

    @command_foundry.command(name="online")
    async def activity_users(self, ctx: commands.Context):
        """List users connected to Foundry"""
        async with self.config.messages() as messages:
            users = await self.wm_api.management.foundry.activity()
            if users['users']:
                await ctx.send(messages['foundry.activity.users'] % ', '.join(users['users']))
            else:
                await ctx.send(messages['foundry.activity.no_users'])

    @command_foundry.command(name="restart")
    async def command_restart(self, ctx: commands.Context):
        """Restart FoundryVTT"""
        await self.discord_api_wrapper(ctx, 'foundry.restart', lambda: self.wm_api.management.foundry.restart())

    @command_foundry.group(name="backup", invoke_without_command=True)
    async def foundry_backup(self, ctx: commands.Context, schemas: Optional[str]):
        """Perform a backup of FoundryVTT. Beware that Foundry WILL BE STOPPED"""

        config = Config()
        config.set('redis.endpoint', await self.config.redis.endpoint())

        queue = Queue(config)
        await queue.put(JobDefinition('foundry.backup',
                                      schemas=[s.strip() for s in schemas.split(',')] if schemas else ['world'],
                                      reaction_msg={
                                          'channel_id': ctx.channel.id,
                                          'message_id': ctx.message.id
                                      }))

        await ctx.message.add_reaction('\U0001F4C5')
