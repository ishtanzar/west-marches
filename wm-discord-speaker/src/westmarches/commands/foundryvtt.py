import logging
import os

import requests
from redbot.core import commands, checks

from westmarches.utils import CompositeMetaClass, MixinMeta, DiscordProgress

log = logging.getLogger("red.westmarches.foundry")


class FoundryCommands(MixinMeta, metaclass=CompositeMetaClass):

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
        async with DiscordProgress(ctx, self.config, "foundry.restart"):
            requests.post(self.foundry_url + '/container/restart/foundry', auth=self.foundry_auth)

    @command_foundry.command(name="backup")
    async def foundry_backup(self, ctx: commands.Context):
        """Perform a backup of FoundryVTT. Beware that Foundry WILL BE STOPPED"""
        async with DiscordProgress(ctx, self.config, "foundry.backup"):
            requests.post(self.foundry_url + '/backup/perform', auth=self.foundry_auth)
