import random

from discord import ChannelType
from redbot.core import commands, checks

from westmarches.utils import CompositeMetaClass, MixinMeta


class RumorsCommands(MixinMeta, metaclass=CompositeMetaClass):

    def __init__(self) -> None:
        super().__init__()

    @commands.group(invoke_without_command=True)
    async def rumors(self, ctx: commands.Context):
        """Get a rumor from the West-Marches"""
        async with self.config.taverns() as taverns:
            if ctx.channel.type is ChannelType.text and ctx.channel.id in taverns:
                await ctx.send(random.choice(await self.config.rumors()))

    @checks.is_owner()
    @rumors.command("add")
    async def add_rumor(self, ctx: commands.Context, *new_rumor):
        """Add a new rumor"""
        async with self.config.rumors() as rumors:
            rumors.append(" ".join(new_rumor))
        await ctx.send("Nouvelle rumeur enregistrée.")

    @checks.is_owner()
    @rumors.command("ls")
    async def list_rumors(self, ctx: commands.Context):
        """List all rumors"""
        async with self.config.rumors() as rumors:
            for i, rumor in enumerate(rumors):
                await ctx.send('{} - {}'.format(i, rumor))

    @checks.is_owner()
    @rumors.command("rm")
    async def del_rumor(self, ctx: commands.Context, rumor_id: int):
        """Remove a rumor"""
        async with self.config.rumors() as rumors:
            old_rumor = rumors[rumor_id]
            del rumors[rumor_id]
            self.config.rumors.set(rumors)

        await ctx.send("Rumeur supprimée : {}".format(old_rumor))

    @checks.is_owner()
    @rumors.command("listen")
    async def rumors_listen(self, ctx: commands.Context):
        """Tell the bot to listen pings in current channel"""
        if ctx.channel.type is ChannelType.text:
            async with self.config.taverns() as taverns:
                taverns.append(ctx.channel.id)
