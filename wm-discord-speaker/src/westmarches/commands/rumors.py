import random

from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

from westmarches import MixinMeta
from westmarches.utils import CompositeMetaClass


class RumorsCommands(MixinMeta, metaclass=CompositeMetaClass):

    def __init__(self) -> None:
        super().__init__()

    @commands.group(invoke_without_command=True)
    async def rumors(self, ctx: commands.Context):
        await ctx.send(random.choice(await self.config.rumors()))

    @rumors.command("add")
    async def add_rumor(self, ctx: commands.Context, *new_rumor):
        async with self.config.rumors() as rumors:
            rumors.append(" ".join(new_rumor))
        await ctx.send("Nouvelle rumeur enregistrée.")

    @rumors.command("ls")
    async def list_rumors(self, ctx: commands.Context):
        async with self.config.rumors() as rumors:
            indexed_rumors = []
            for i, rumor in enumerate(rumors):
                indexed_rumors.append('{} - {}'.format(i, rumor))
            for page in pagify(", ".join(indexed_rumors), delims=[", ", "\n"], page_length=120):
                await ctx.send(page)

    @rumors.command("rm")
    async def del_rumor(self, ctx: commands.Context, rumor_id: int):
        old_rumor = None

        async with self.config.rumors() as rumors:
            old_rumor = rumors[rumor_id]
            del rumors[rumor_id]
            self.config.rumors.set(rumors)

        await ctx.send("Rumeur supprimée : {}".format(old_rumor))
