import datetime
import logging
import os
from abc import abstractmethod

from discord.ext.commands import Context
from redbot.core import commands, checks

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

    @checks.has_permissions(administrator=True)
    @commands.group(name="foundry")
    async def command_foundry(self, ctx: commands.Context):
        """Foundry admin commands"""

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
