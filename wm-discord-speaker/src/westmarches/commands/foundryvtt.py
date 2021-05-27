from redbot.core import commands

from westmarches import MixinMeta
from westmarches.utils import CompositeMetaClass


class FoundryCommands(MixinMeta, metaclass=CompositeMetaClass):

    @commands.group(name="foundry")
    async def command_foundry(self):
        """Foundry admin commands"""

    @command_foundry.command(name="restart")
    async def command_restart(self):
        pass
