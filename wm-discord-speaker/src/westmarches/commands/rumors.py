import datetime
import random

from discord import ChannelType, TextChannel
from redbot.core import commands, checks

from westmarches.utils import CompositeMetaClass, MixinMeta


class RumorsCommands(MixinMeta, metaclass=CompositeMetaClass):

    def __init__(self) -> None:
        super().__init__()

    @checks.has_permissions(administrator=True)
    @commands.group(invoke_without_command=True)
    async def rumors(self, ctx: commands.Context):
        """Get a rumor from the West Marches"""
        async with self.config.taverns() as taverns, self.config.rumors() as rumors, self.config.rumors_triggers() as triggers:
            triggers: dict

            now = datetime.datetime.now()
            reset_delta = datetime.timedelta(hours=2)

            if ctx.channel.id in taverns:
                key = await self.config.rumors_idx()
                user_id = str(ctx.author.id)
                (trigger_count, trigger_ts) = triggers[user_id] if user_id in triggers else (0, 0)

                trigger_date = datetime.datetime.fromtimestamp(trigger_ts)
                if trigger_date + reset_delta < now:
                    trigger_count = 0
                    trigger_date = now

                if trigger_count < 3:
                    await ctx.send(rumors[key])

                    triggers[user_id] = (trigger_count + 1, trigger_date.timestamp())
                    await self.config.rumors_idx.set(key - 1 if key >= 1 else len(rumors) - 1)
                    await self.config.rumors_triggers.set(triggers)
                else:
                    async with self.config.rumors_cooldown_message() as messages:
                        await ctx.send(random.choice(messages))

    @rumors.command("push")
    async def push_rumor(self, ctx: commands.Context):
        """Push current rumor to all taverns"""
        async with self.config.taverns() as taverns, self.config.rumors() as rumors:
            key = await self.config.rumors_idx()

            for tavern in taverns:
                channel: TextChannel = self.bot.get_channel(tavern)
                if channel:
                    await channel.send(rumors[key])

            await self.config.rumors_idx.set(key - 1 if key >= 1 else len(rumors) - 1)

    @rumors.command("add")
    async def add_rumor(self, ctx: commands.Context, *new_rumor):
        """Add a new rumor"""
        async with self.config.rumors() as rumors:
            rumors.append(" ".join(new_rumor))
            await self.config.rumors_idx.set(len(rumors))
        await ctx.send("Nouvelle rumeur enregistrée, pointeur remis à zéro.")

    @rumors.command("list", aliases=["ls"])
    async def list_rumors(self, ctx: commands.Context):
        """List all rumors"""
        key = await self.config.rumors_idx()
        async with self.config.rumors() as rumors:
            for i, rumor in enumerate(rumors):
                await ctx.send('{}{} - {}'.format(i, "**" if key == i else "", rumor))

    @rumors.command("reset")
    async def reset_rumors_key(self, ctx: commands.Context):
        """Reset the rumors key to the latest"""
        async with self.config.rumors() as rumors:
            await self.config.rumors_idx.set(len(rumors) - 1)
            await ctx.send("Pointeur remis à zéro.")

    @rumors.command("delete", aliases=["rm", "del"])
    async def del_rumor(self, ctx: commands.Context, rumor_id: int):
        """Remove a rumor"""
        async with self.config.rumors() as rumors:
            old_rumor = rumors[rumor_id]
            del rumors[rumor_id]
            await self.config.rumors.set(rumors)
            await self.config.rumors_idx.set(len(rumors))

        await ctx.send("Rumeur supprimée : {}, pointeur remis à zéro.".format(old_rumor))

    @rumors.command("listen")
    async def rumors_listen(self, ctx: commands.Context):
        """Tell the bot to listen pings in current channel"""
        if ctx.channel.type is ChannelType.text:
            async with self.config.taverns() as taverns:
                taverns.append(ctx.channel.id)
            await ctx.send("Nouvelle taverne enregistrée.")
