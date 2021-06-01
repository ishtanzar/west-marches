import logging
import os

import requests
from redbot.core import commands, checks

from westmarches.utils import CompositeMetaClass, MixinMeta

log = logging.getLogger("red.westmarches.foundry")


class FoundryCommands(MixinMeta, metaclass=CompositeMetaClass):

    def __init__(self) -> None:
        super().__init__()

    @property
    def foundry_url(self):
        return 'http://{}:5000'.format(os.environ['FOUNDRY_HOST'])

    @property
    def foundry_auth(self):
        return 'foundry_manager', os.environ['MANAGER_API_SECRET']

    @commands.group(name="foundry")
    async def command_foundry(self, ctx: commands.Context):
        """Foundry admin commands"""

    @checks.is_owner()
    @command_foundry.command(name="restart")
    async def command_restart(self, ctx: commands.Context):
        """Restart FoundryVTT"""
        await ctx.send("Krusk, ça sent encore le cramé; ouvre la fenêtre !")
        log.warning({"who": str(ctx.message.author), "what": "foundry.restart"})
        requests.post(self.foundry_url + '/container/restart/foundry', auth=self.foundry_auth)
        await ctx.send('Merci')
